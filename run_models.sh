#!/bin/bash

# Change directory to the location of the Python script

# Activate a virtual environment if needed (uncomment the line below and replace with your virtual environment path)
# source /path/to/your/virtual/env/bin/activate

# Run the Python script
python savePredictions.py

# Deactivate the virtual environment if it was activated (uncomment the line below if you activated the virtual environment)
# deactivate

echo "Prediction generation completed at $(date)"
