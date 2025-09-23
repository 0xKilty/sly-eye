import docker
import json
import logging
logger = logging.getLogger("sly-eye")

def run_trufflehog(image):
    client = docker.from_env()

    trufflehog_image = "trufflesecurity/trufflehog:latest"
    logger.debug(f"Pulling image: {trufflehog_image}")
    client.images.pull(trufflehog_image)

    logger.debug("Starting trufflehog container")

    params = f"docker --image {image} --json"
    logger.debug(f"Running: trufflehog {params}")
    container = client.containers.run(trufflehog_image, params.split(" "), remove=True)

    logger.debug("Stopping trufflehog container")
    ret =  [json.loads(line) for line in container.decode().splitlines()]
    return ret