# To generate predictions in bulk 

import predictionModel as ml
import pandas as pd
import os
import datetime
import logging
from datetime import datetime, timedelta
import redis
from dotenv import load_dotenv
load_dotenv(".config")
import json

def check():
  required_envs = ["ENTSOE_TOKEN"]
  missing_vars = [var for var in required_envs if os.getenv(var) is None]
  if missing_vars:
    raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")
  
  required_folders = ["./data/logs","./data/predictions"]
  for folder_path in required_folders:
    if not os.path.exists(folder_path):
      os.makedirs(folder_path)
      print(f"Created folder: {folder_path}")

  requiredBlankFiles = []
  for reqf in requiredBlankFiles :
    if not os.path.exists(reqf):
      open(reqf, 'w').close()
  
  checkRedis()

def checkRedis():
  try:
    redis_url = os.getenv("PREDICTIONS_REDIS_URL")
    r = redis.from_url(redis_url)
    print(r.ping())
  except Exception:
    print("Error in connecting to redis server")

def getFolderPath(type):
   types = {
      "predictions": "./data/predictions",
      "log" : "./data/logs"
   }
   return types[type]

def getLogFileName(country):
    current_month = datetime.now().strftime('%m')
    current_year = datetime.now().strftime('%Y')
    file_name = f"{country}-{current_month}-{current_year}.log"
    folder_path = getFolderPath("log")
    file_path = os.path.join(folder_path, file_name)
    if not os.path.exists(file_path):
        open(file_path, 'w').close()
    return file_path


def logPrediction(response):
    logFileName = getLogFileName(response["input"]["country"])
    # logging.basicConfig(filename=logFileName, format='%(asctime)s -  %(message)s', level=logging.INFO )
    ouputString = response["output"]["percentRenewableForecast"].tolist()
    # model-name input_starttime input_endtime input[] output[]
    logString = str(datetime.now())+" : "+response["input"]["model"]+ " "+str(response["input"]["start"])+" "+str(response["input"]["end"])+" "+str(response["input"]["percentRenewable"])+" "+str(ouputString)+"\n"
    # print(logString)
    # logging.info(logString+"")
    with open(logFileName, 'a') as log_file:
      log_file.write(logString)


def get_start_end_dates():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=7)
    end_date = today + timedelta(days=7)
    return start_date, end_date

def savePredictionsToFile(response):
    file_name = response["input"]["country"]+".csv"
    folder_path =  getFolderPath("predictions")
    file_path = os.path.join(folder_path,file_name)
    if not os.path.exists(file_path):
        open(file_path, 'w').close()

    try:
      oldData = pd.read_csv(folder_path+"/"+file_name)
      # print(oldData)
    except pd.errors.EmptyDataError:
      oldData = pd.DataFrame(columns=['startTime', 'percentRenewableForecast'])
    
    oldData["startTime"] =  pd.to_datetime(oldData['startTime']) # .dt.strftime('%Y%m%d%H%M')
    # print(oldData)
    newData = response["output"]
    newData["startTime"] =  pd.to_datetime(newData['startTime']) # .dt.strftime('%Y%m%d%H%M')
    # print(newData)
    mergedData = pd.concat([oldData,newData]).drop_duplicates(subset="startTime",keep='last')
    # print(mergedData)

    start_date, end_date = get_start_end_dates()
    # Filter the merged DataFrame
    filteredData = mergedData[(mergedData['startTime'] >= start_date) & (mergedData['startTime'] <= end_date)]
    # filteredData['startTime'] = filteredData['startTime'].dt.strftime('%Y%m%d%H%M')
    # filteredData.to_csv(file_path, index=False, mode='w')
    mergedData.to_csv(file_path, index=False, mode='w')


def savePredictionsToRedis(response):
  key_name = response["input"]["country"]+"_forecast"
  newData = response["output"]
  newData["startTime"] =  pd.to_datetime(newData['startTime']).astype("str")
  forecast_data =  {
    "data": newData.to_dict(),
    "timeInterval": 60,
  }
  last_update = str(datetime.now())
  cached_object = {
      "data": forecast_data["data"],
      "timeInterval": forecast_data["timeInterval"],
      "last_updated": last_update,
  }
  redis_url = os.getenv("PREDICTIONS_REDIS_URL")
  r = redis.from_url(redis_url)
  r.set(key_name, json.dumps(cached_object))

def main():
  print("Starting checks....")
  check()
  print("Checks done....")
  countryList = ml.model_get_available_country_list()
  for country in countryList:
    print("Running for "+country)
    predictions = ml.model_run_latest(country)
    #print(predictions)
    savePredictionsToFile(predictions)
    savePredictionsToRedis(predictions)
    logPrediction(predictions)
  print("Done!")

if __name__ == "__main__":
  main()