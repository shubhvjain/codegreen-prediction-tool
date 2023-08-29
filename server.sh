#!/bin/bash

docker_image="codegreen-prediction-server"
container_name="codegreen-prediction-server"

config_file=".config"

if [ -e "$config_file" ]; then
    # Load environment variables from the .config file
    source "$config_file"    
    echo "Config file loaded"
else
    echo "Error: $config_file file does not exist."
    exit 1
fi


echo "====Building docker image===="

docker build -t codegreen-prediction-server -f Dockerfile.server .

echo "====Creating a new container===="

if docker ps -a --format "{{.Names}}" | grep -q "^$container_name$"; then
    docker stop "$container_name" && docker rm "$container_name"
    echo "Container $container_name has been stopped and removed."
else
    echo "Container $container_name does not exist."
fi

docker create --name "$container_name" -v "$PREDICTIONS_DOCKER_VOLUME_PATH:/app/data" "$docker_image" 

# docker network connect "$GREENERAI_DOCKER_NETWORK" "$container_name"
docker start "$container_name" 

sleep 30 
# sleep 10800
docker stop codegreen-prediction-server
# echo "docker run --network greenerai_default --name $container_name  -v $PREDICTIONS_DOCKER_VOLUME_PATH:/app/data $docker_image"
# docker compose build
# docker run --name "$container_name"  --network "greenerai"  -v "$PREDICTIONS_DOCKER_VOLUME_PATH:/app/data" "$docker_image" 
# docker network connect greenerai "$container_name"
