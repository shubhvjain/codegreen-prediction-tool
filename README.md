# Codegreen-prediction-tool
Python project to deploy renewable energy prediction models 

# Installation and setup
- **Pre-requisites**:
  - Docker must be installed 
  - The [Codegreen server](https://github.com/AnneHartebrodt/codegreen) must be up and running 
- **Clone the repository** : `git clone https://github.com/shubhvjain/codegreen-prediction-tool.git`
- **Generate the config file** : 
  - Create a new file named  `.config`  in the root of the project repository
  - Initialize the file will the following envirenment variables:
  ```
  ENTSOE_TOKEN=token
  PREDICTIONS_REDIS_URL="redis://cache:6379"
  PREDICTIONS_CRON_JOB_FREQ_HOUR=1
  PREDICTIONS_DOCKER_VOLUME_PATH="/full/local/path"
  GREENERAI_DOCKER_NETWORK=greenerai_default
  ```
- **Initial setup** :  Run `./bin/initial-setup.sh`. 
  - **Note** : This command must be run again if config files are changed
  - **Test run the program** : Before setting up the cron job, to ensure everything is configured correctly, run `./bin/run.sh`
- **Setting up the cron job** : Run `./bin/schedule.sh`. The frequency of the job is read from the `PREDICTIONS_CRON_JOB_FREQ_HOUR` variable in the `.config` file

# Development 

## Folder structure 
- `bin` : contains 
- `models`




tool 
extention to the main codegreen service 
deploys prediction models in a more sustinable 