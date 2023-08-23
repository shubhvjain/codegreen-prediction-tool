#!/bin/bash

conda create -n bionet23 python=3.8
conda activate bionet23
pip install -r requirements.txt
# Display the message
echo "Use the 'bionet23' environment. It has been activated and required dependencies are installed."
