# Codegreen-prediction-tool
Python project to deploy renewable energy prediction models 

# Installation and setup
- **Pre-requisites**:
  - Docker must be installed 
  - The [Codegreen server](https://github.com/AnneHartebrodt/codegreen) must be up and running
  - Obtain the name of the Docker network in which the Codegreen containers exist. Use the command `docker network ls`. Usually, the default network name is `projectfoldername_default`.
- **Clone the repository** : `git clone https://github.com/shubhvjain/codegreen-prediction-tool.git`. All further steps must be performed from the root of the project folder. 
- **Create a config file** : 
  - Create a new file named  `.config`  in the root of the project repository
  - Initialize the file will the following envirenment variables:
  ```env
  ENTSOE_TOKEN=token
  PREDICTIONS_REDIS_URL="redis://cache:6379"
  PREDICTIONS_CRON_JOB_FREQ_HOUR=1
  PREDICTIONS_DOCKER_VOLUME_PATH="/full/local/path"
  GREENERAI_DOCKER_NETWORK=greenerai_default
  ```
  
- **Initial setup** :  Execute the initial setup by running `./setup.sh`.
  - **Note** : This command must be run again if config files are changed
  - **Test run the program** : Before configuring the cron job, ensure everything is properly set up by running `./run.sh`. If the setup is correct, you will find log files of models run successfully in the path specified in the config file.
- **Setting up the cron job** : Execute `./schedule.sh` to set up the cron job. The frequency of the job is determined by the `PREDICTIONS_CRON_JOB_FREQ_HOUR` variable in the `.config` file.

# Development 

- Description of each variable required in the `.config` file:
  - `ENTSOE_TOKEN`: Token required to access the ENTSO-E API.
  - `PREDICTIONS_REDIS_URL`: The URL of the common Redis server. Use "redis://cache:6379".
  - `PREDICTIONS_CRON_JOB_FREQ_HOUR`: The frequency (in hours) of the CRON job configured in the last step of installation.
  - `PREDICTIONS_DOCKER_VOLUME_PATH`: The full path on the host machine where the recent prediction files and log files will be stored.
  - `GREENERAI_DOCKER_NETWORK`: The name of the Docker network in which CodeGreen containers are running.
