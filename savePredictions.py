"""This file contains the scripts that will be run to generate prediction models for all avaialbe countries. the values will be stored in the csv file and saved to a redis server. each run is also stored in a log file 
"""

import pandas as pd
import os
import datetime
from datetime import datetime, timedelta
import redis
import json
from dotenv import load_dotenv
import predictionModel as ml


def loadEnv():
    """This method loads the environment variables stored in the `.config` file at the root of the project. """
    load_dotenv(".config")


def check():
    """This method ensures that everything is properly configured before advancing to execute prediction models. 
    This includes:
    - Confirming the existence of necessary environment variables.
    - Validating the presence of required folders. Two folders, namely `logs` and `predictions`, should be present within the `data` folder.
    - Verifying the availability of the Redis server.
    """
    required_envs = ["ENTSOE_TOKEN"]
    missing_vars = [var for var in required_envs if os.getenv(var) is None]
    if missing_vars:
        raise EnvironmentError(
            f"Missing environment variables: {', '.join(missing_vars)}")

    required_folders = ["./data/logs", "./data/predictions"]
    for folder_path in required_folders:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created folder: {folder_path}")

    requiredBlankFiles = []
    for reqf in requiredBlankFiles:
        if not os.path.exists(reqf):
            open(reqf, 'w').close()

    checkRedis()


def checkRedis():
    """This method check the availability of Redis server"""
    try:
        redis_url = os.getenv("PREDICTIONS_REDIS_URL")
        r = redis.from_url(redis_url)
        print(r.ping())
    except Exception:
        print("Error in connecting to redis server")


def getLogFileName(country):
    """Returns the current  log file name for the specified country. 
    It the file doesn't exists, a blank file will be created.
    Logs records are stored in simple text files within the 'logs' folder located inside the 'data' folder. 
    The names of file have the format : "country code-current month-current year", 
    guaranteeing a distinct log file for each country and month of the year. 
    """
    current_month = datetime.now().strftime('%m')
    current_year = datetime.now().strftime('%Y')
    file_name = f"{country}-{current_month}-{current_year}.log"
    folder_path = "./data/logs"
    file_path = os.path.join(folder_path, file_name)
    if not os.path.exists(file_path):
        open(file_path, 'w').close()
    return file_path


def logPrediction(response):
    """This method logs predictions made by a model. It requires the full response of the run model method
    response format : { "input": { "country":"", "model":"", "start":"", "end":"",  "percentRenewable":[],  } , "output": <pandas dataframe> }
    Log entry format (single line) : timestamp : model-name input_starttime_UTC  input_endtime_UTC input(percent renewable )[] output[](percent renewable values for next 48 hours)
    """
    logFileName = getLogFileName(response["input"]["country"])
    ouputString = response["output"]["percentRenewableForecast"].tolist()
    logString = str(datetime.now())+" : "+response["input"]["model"] + " "+str(response["input"]["start"])+" "+str(
        response["input"]["end"])+" "+str(response["input"]["percentRenewable"])+" "+str(ouputString)+"\n"
    with open(logFileName, 'a') as log_file:
        log_file.write(logString)


def get_start_end_dates():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=7)
    end_date = today + timedelta(days=7)
    return start_date, end_date


def savePredictionsToFile(response):
    file_name = response["input"]["country"]+".csv"
    folder_path = "./data/predictions"
    file_path = os.path.join(folder_path, file_name)
    if not os.path.exists(file_path):
        open(file_path, 'w').close()

    try:
        oldData = pd.read_csv(folder_path+"/"+file_name)
    except pd.errors.EmptyDataError:
        oldData = pd.DataFrame(
            columns=['startTimeUTC', 'percentRenewableForecast'])

    oldData["startTimeUTC"] = pd.to_datetime(oldData['startTimeUTC'])  
    newData = response["output"]
    newData["startTimeUTC"] = pd.to_datetime(newData['startTimeUTC'])
    mergedData = pd.concat([oldData, newData]).drop_duplicates(
        subset="startTimeUTC", keep='last')

    start_date, end_date = get_start_end_dates()
    # Filter the merged DataFrame
    filteredData = mergedData[(mergedData['startTimeUTC'] >= start_date) & (
        mergedData['startTimeUTC'] <= end_date)]
    # filteredData['startTimeUTC'] = filteredData['startTimeUTC'].dt.strftime('%Y%m%d%H%M')
    # filteredData.to_csv(file_path, index=False, mode='w')
    mergedData.to_csv(file_path, index=False, mode='w')


def savePredictionsToRedis(response):
    key_name = response["input"]["country"]+"_forecast"
    newData = response["output"]
    newData["startTimeUTC"] = newData['startTimeUTC'].dt.strftime('%Y%m%d%H%M').astype("str")
    last_update = str(datetime.now())
    cached_object = {
        "data": newData.to_dict(),
        "timeInterval": 60,
        "last_updated": last_update,
    }
    # print(cached_object)
    try : 
        redis_url = os.getenv("PREDICTIONS_REDIS_URL")
        r = redis.from_url(redis_url)
        r.set(key_name, json.dumps(cached_object))
    except Exception :
        print("Error in saving data Redis cache")

def main():
    """This is the main script"""
    # load config file
    loadEnv()
    print("Starting checks....")
    check()
    print("Checks done....")
    # get list of available models 
    countryList = ml.get_available_country_list()
    for country in countryList:
        print("Running for "+country)
        # run model and stored it in csv file and to the redis server and log it
        predictions = ml.run_latest_model(country)
        savePredictionsToFile(predictions)
        savePredictionsToRedis(predictions)
        logPrediction(predictions)
    print("Done!")


if __name__ == "__main__":
    main()
