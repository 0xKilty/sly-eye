import docker
import time
from elasticsearch import Elasticsearch
import logging
logger = logging.getLogger("sly-eye")

NETWORK = "elasticnet"
ELASTIC_CONTAINER_NAME = "es01"

def start_elastic_network(client, name=NETWORK):
    try:
        client.networks.get(name)
    except docker.errors.NotFound:
        logger.debug(f"Creating network: {name}")
        client.networks.create(name, driver="bridge")

def start_elastic():
    client = docker.from_env()
    start_elastic_network(client)

    image = "docker.elastic.co/elasticsearch/elasticsearch:8.15.3"
    try:
        client.images.get(image)
    except docker.errors.ImageNotFound:
        logger.debug(f"Pulling image: {image}")
        client.images.pull(image)

    vol_name = "esdata"
    try:
        client.volumes.get(vol_name)
    except docker.errors.NotFound:
        logger.debug(f"Creating volume: {vol_name}")
        client.volumes.create(name=vol_name)

    try:
        old = client.containers.get(ELASTIC_CONTAINER_NAME)
        logger.debug("Removing existing elastic container")
        old.remove(force=True)
    except:
        pass

    env = {
        "discovery.type": "single-node",
        "xpack.security.enabled": "false",
        "xpack.security.enrollment.enabled": "false",
        "xpack.security.autoconfiguration.enabled": "false",
        "ES_JAVA_OPTS": "-Xms512m -Xmx512m",
    }

    logger.debug(f"Starting elastic container")
    container = client.containers.run(
        image,
        name=ELASTIC_CONTAINER_NAME,
        detach=True,
        environment=env,
        ports={"9200/tcp": 9200},
        volumes={vol_name: {"bind": "/usr/share/elasticsearch/data", "mode": "rw"}},
        network=NETWORK, 
        hostname=ELASTIC_CONTAINER_NAME
    )

    url = "http://localhost:9200"
    logger.debug(f"Attempting to connect to elastic search: {url}")
    es = Elasticsearch(url)
    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            info = es.info()
            logger.debug(f"Elasticsearch is up v{info['version']['number']}")
            return es, container
        except Exception:
            time.sleep(1)

    raise RuntimeError("Elasticsearch did not become ready in time")

def stop_elastic(container):
    try:
        logger.debug(f"Stopping Elasticsearch container: {container.name}")
        container.stop(timeout=10)
        container.remove(force=True)
    except Exception as e:
        logger.warning(f"Failed to stop container cleanly: {e}")
