import docker
import os

def run_trufflehog():
    client = docker.from_env()

    container = client.containers.run(
        "trufflesecurity/trufflehog:latest",
        [
            "github",
            "--repo", "https://github.com/trufflesecurity/test_keys"
        ],
        volumes={
            os.getcwd(): {  # mount current dir
                'bind': '/pwd',
                'mode': 'rw'
            }
        },
        remove=True,   # equivalent to --rm
        tty=True,      # equivalent to -t
        stdin_open=True  # equivalent to -i
    )