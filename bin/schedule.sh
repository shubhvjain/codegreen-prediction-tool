#!/bin/bash

docker_image="codegreen-prediction-tool"
container_name="codegreen-prediction-tool"
config_file=".config"

if [ -e "$config_file" ]; then
    # Load environment variables from the .config file
    source "$config_file"    
    echo "Config file loaded"
else
    echo "Error: $config_file file does not exist."
    exit 1
fi

run_script_full_path=$(pwd)/bin/run.sh
cron_log_full_path=$(pwd)/cron-run.log




# Check if a cron job is already set up
existing_cron_job=$(crontab -l | grep "$run_script_full_path")
if [ -n "$existing_cron_job" ]; then
    echo "Currently running cron job details:"
    echo "$existing_cron_job"
fi

# Validate the input
if ! [[ "$PREDICTIONS_CRON_JOB_FREQ_HOUR" =~ ^[0-9]+$ && "$PREDICTIONS_CRON_JOB_FREQ_HOUR" -ge 1 && "$PREDICTIONS_CRON_JOB_FREQ_HOUR" -le 24 ]]; then
    echo "Invalid frequency. Please enter a valid number between 1 and 24."
    exit 1
fi

# Set up or modify the cron job
cron_command="bash $run_script_full_path >> $cron_log_full_path"  # Replace with the actual path to run_model.sh
# existing_cron_job_line="0 */$PREDICTIONS_CRON_JOB_FREQ_HOUR * * * $cron_command"
existing_cron_job_line="*/$PREDICTIONS_CRON_JOB_FREQ_HOUR * * * * $cron_command"


# Remove any existing cron job with the same command
crontab -l | grep -v "$cron_command" | crontab -

# Add the new cron job
echo "$existing_cron_job_line" | crontab -

# Get the PID of the newly added cron job

echo "Cron job set up successfully with a frequency of $PREDICTIONS_CRON_JOB_FREQ_HOUR hours!"

