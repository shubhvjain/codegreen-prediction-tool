#!/bin/bash

# Display initial message
echo "Hello, this script will allow you to create or modify the schedule for running prediction models for all countries"

# Check if a cron job is already set up
existing_cron_job=$(crontab -l | grep "run_models.sh")
if [ -n "$existing_cron_job" ]; then
    echo "Currently running cron job details:"
    echo "$existing_cron_job"
    echo "You have an existing cron job. You can modify it or set up a new one."
fi

# Prompt user for frequency
read -p "Enter the frequency of running the script in hours (1-24): " frequency

# Validate the input
if ! [[ "$frequency" =~ ^[0-9]+$ && "$frequency" -ge 1 && "$frequency" -le 24 ]]; then
    echo "Invalid input. Please enter a valid number between 1 and 24."
    exit 1
fi

# Set up or modify the cron job
cron_command="bash run_models.sh"  # Replace with the actual path to run_model.sh
existing_cron_job_line="0 */$frequency * * * $cron_command"

# Remove any existing cron job with the same command
crontab -l | grep -v "$cron_command" | crontab -

# Add the new cron job
echo "$existing_cron_job_line" | crontab -

# Get the PID of the newly added cron job
new_pid=$(ps aux | grep "$cron_command" | grep -v "grep" | awk '{print $2}')

echo "Cron job set up successfully with a frequency of $frequency hours!"
echo "Process ID (PID) of the cron job: $new_pid"
