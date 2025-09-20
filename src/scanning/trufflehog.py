import docker
import os

def run_trufflehog():
    client = docker.from_env()

    image = "trufflesecurity/trufflehog:latest"
    client.images.pull(image)

    container = client.containers.run(
        image,
        [
            "github",
            "--repo", 
            "https://github.com/trufflesecurity/test_keys",
            "--json"
        ],
        remove=True,
    )

    print(container)