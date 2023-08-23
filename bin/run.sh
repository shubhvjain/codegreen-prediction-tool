#!/bin/bash
echo "Running Prediction models at $(date)"
container_name="codegreen-prediction-tool"
docker start "$container_name" 