import docker
import json
import subprocess
import logging
logger = logging.getLogger("sly-eye")

class TruffleHog:
    def __init__(self):
        self.client = docker.from_env()  
        self.trufflehog_image = "trufflesecurity/trufflehog:latest"
        
        try:
            self.client.images.get(self.trufflehog_image)
        except docker.errors.ImageNotFound:
            logger.debug(f"Pulling image: {self.trufflehog_image}")
            self.client.images.pull(self.trufflehog_image)

    def run_trufflehog(self, image):
        logger.debug("Starting trufflehog container")

        params = f"docker --image {image} --json"
        logger.debug(f"Running: trufflehog {params}")

        logs = self.client.containers.run(
            self.trufflehog_image,
            params.split(" "),
            remove=True,
            stdout=True,
            stderr=True,
            stream=True,
            environment={"TRUFFLEHOG_NO_UPDATE": "true"},
        )

        results = []
        for line in logs:
            try:
                results.append(json.loads(line.decode()))
            except json.JSONDecodeError:
                pass

        return results
    
def run_trufflehog(image):
    command = f"trufflehog docker --image {image} --json"

    logger.debug(f"Running: {command}")

    process = subprocess.Popen(
        command.split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )

    process.wait()

    results = []
    for line in process.stdout:
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            logger.debug(f"Non-JSON line: {line.strip()}")

    stderr = process.stderr.read()
    if stderr:
        logger.warning(f"Trufflehog stderr: {stderr}")

    return results