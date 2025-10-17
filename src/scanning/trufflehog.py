import docker
import json
import sys
import logging
import signal
import atexit

logger = logging.getLogger("sly-eye")

class TruffleHog:
    def __init__(self):
        self.client = docker.from_env()  
        self.trufflehog_image = "trufflesecurity/trufflehog:latest"
        self._active_containers = []
        
        try:
            self.client.images.get(self.trufflehog_image)
        except docker.errors.ImageNotFound:
            logger.debug(f"Pulling image: {self.trufflehog_image}")
            self.client.images.pull(self.trufflehog_image)
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self.cleanup)


    def run_trufflehog(self, image):
        logger.debug("Starting trufflehog container")

        params = f"docker --image {image} --json"
        logger.debug(f"Running: trufflehog {params}")

        container = None
        results = []

        try:
            container = self.client.containers.run(
                self.trufflehog_image,
                params.split(" "),
                detach=True,
                stdout=True,
                stderr=True,
                environment={"TRUFFLEHOG_NO_UPDATE": "true"},
            )

            self._active_containers.append(container)

            try:
                for line in container.logs(stream=True, follow=True):
                    try:
                        results.append(json.loads(line.decode()))
                    except json.JSONDecodeError:
                        continue
            except docker.errors.APIError as e:
                logger.warning(f"Failed to stream logs for {image}: {e}")

            try:
                exit_status = container.wait()
            except docker.errors.APIError as e:
                logger.warning(f"Failed to get exit status for {image}: {e}")
                exit_status = {}

            status_code = exit_status.get("StatusCode") if isinstance(exit_status, dict) else None
            if status_code not in (None, 0):
                logger.debug(f"TruffleHog exited with status {status_code} for {image}")

            return results
        finally:
            if container is not None:
                try:
                    self._active_containers.remove(container)
                except ValueError:
                    pass

                try:
                    container.wait(timeout=5)
                except docker.errors.APIError:
                    pass

                try:
                    container.remove(force=True)
                except docker.errors.APIError as e:
                    logger.warning(f"Failed to remove container for {image}: {e}")
                except docker.errors.NotFound:
                    pass
    
    def cleanup(self):
        for c in list(self._active_containers):
            try:
                logger.debug(f"Stopping TruffleHog container: {c.name}")
                c.stop(timeout=5)
                c.remove(force=True)
            except Exception as e:
                logger.warning(f"Failed to stop container {c.name}: {e}")
        self._active_containers.clear()


    def _signal_handler(self, signum, frame):
        logger.warning(f"Received signal {signum} — cleaning up TruffleHog containers...")
        self.cleanup()
        sys.exit(0)
