#!/bin/bash
echo "==="
echo "Running Prediction generation at $(date)"

conda  init bash
source ~/.bash_profile
## call run_models.sh PREDICTIONS/REPO/FOLDER/PATH
# Change directory to the location of the Python script
#cd "$PREDICTIONS_REPO_FOLDER_PATH"
# cd $1
# pwd
# source .env
cd ~/code/bionets/codegreen-prediction-tool
# Activate a virtual environment if needed (uncomment the line below and replace with your virtual environment path)
# source /path/to/your/virtual/env/bin/activate
conda activate xML

# Run the Python script
python savePredictions.py

# Deactivate the virtual environment if it was activated (uncomment the line below if you activated the virtual environment)
# conda deactivate

echo "Prediction generation completed at $(date)"
