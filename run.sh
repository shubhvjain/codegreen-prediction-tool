#!/bin/bash
source ~/.bash_profile
export PATH="/usr/local/bin:$PATH"
echo "$(date): Running Prediction models"
container_name="codegreen-prediction-tool"
docker start "$container_name" 