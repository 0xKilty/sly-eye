'''

docker manifest inspect ubuntu:20.04
to get latest hash

docker manifest inspect ubuntu@sha256:c664f8f86ed5a386b0a340d981b8f81714e21a8b9c73f658c4bea56aa179d54a
to get size information

'''

import subprocess
import json

class DockerImage:
    def __init__(self, image):
        self.image = image
        
    def gather_info(self):
        output = subprocess.check_output(
            ["docker", "manifest", "inspect", self.image, "-v"],
            text=True
        )
        
        return json.loads(output)