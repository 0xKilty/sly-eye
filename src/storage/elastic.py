import docker
import time
from elasticsearch import Elasticsearch
import logging
logger = logging.getLogger("sly-eye")

def run_elastic():
    client = docker.from_env()

    image = "docker.elastic.co/elasticsearch/elasticsearch:8.15.3"
    logger.debug(f"Pulling image: {image}")
    client.images.pull(image)

    vol_name = "esdata"
    logger.debug(f"Getting/creating volume: {vol_name}")
    try:
        client.volumes.get(vol_name)
    except docker.errors.NotFound:
        client.volumes.create(name=vol_name)

    container_name = "es01"
    try:
        old = client.containers.get(container_name)
        logger.debug("Removing existing container")
        old.remove(force=True)
    except:
        pass

    env = {
        "discovery.type": "single-node",
        "xpack.security.enabled": "false",
        "ES_JAVA_OPTS": "-Xms512m -Xmx512m"
    }

    logger.debug(f"Starting elastic container")
    container = client.containers.run(
        image,
        name=container_name,
        detach=True,
        environment=env,
        ports={"9200/tcp": 9200},
        volumes={vol_name: {"bind": "/usr/share/elasticsearch/data", "mode": "rw"}},
    )

    url = "http://localhost:9200"
    logger.debug(f"Attempting to connect to elastic search: {url}")
    es = Elasticsearch(url)
    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            info = es.info()
            print("Elasticsearch is up:", info["version"]["number"])
            return es, container
        except Exception as e:
            logger.debug(f"Failed to connect to elastic search {e}")
            time.sleep(2)

    raise RuntimeError("Elasticsearch did not become ready in time")