import docker
import logging
import time

from ..storing.elastic import start_elastic_network, ELASTIC_CONTAINER_NAME, NETWORK

logger = logging.getLogger("sly-eye")

def start_kibana():
    client = docker.from_env()
    start_elastic_network(client)

    image = "docker.elastic.co/kibana/kibana:8.15.3"
    container_name = "kib01"

    logger.debug(f"Pulling Kibana image: {image}")
    client.images.pull(image)

    try:
        old = client.containers.get(container_name)
        logger.debug("Removing existing Kibana container")
        old.remove(force=True)
    except docker.errors.NotFound:
        pass

    env = {
        "ELASTICSEARCH_HOSTS": f"http://{ELASTIC_CONTAINER_NAME}:9200",
        "ELASTICSEARCH_SSL_VERIFICATIONMODE": "none",
        "XPACK_SECURITY_AUTHC_HTTP_ENABLED": "false",
        "XPACK_SECURITY_AUTHC_SELECTOR_ENABLED": "false"
    }

    logger.debug("Starting Kibana container")
    container = client.containers.run(
        image,
        name=container_name,
        detach=True,
        environment=env,
        ports={"5601/tcp": 5601},
        network=NETWORK,
        hostname=container_name
    )

    url = "http://localhost:5601"
    logger.debug(f"Kibana started, waiting until available at {url}")

    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            import requests
            r = requests.get(url)
            if r.status_code == 200:
                logger.debug("Kibana is up and running")
                return container
        except Exception:
            time.sleep(1)

    raise RuntimeError("Kibana did not become ready in time")
