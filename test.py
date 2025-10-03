from src.selecting.docker import DockerImage

image = DockerImage("ubuntu:20.04")

print(image.gather_info())

