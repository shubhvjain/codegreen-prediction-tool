#!/bin/bash
source ~/.bash_profile
export PATH="/usr/local/bin:$PATH"
echo "Running Prediction models at $(date)"
container_name="codegreen-prediction-tool"
docker start "$container_name" 