# To generate predictions in bulk 

import predictionModel as ml
import pandas as pd
import os
import datetime
import logging
from datetime import datetime, timedelta

def getLogFileName(country):
    current_month = datetime.now().strftime('%m')
    current_year = datetime.now().strftime('%Y')
    file_name = f"{country}-{current_month}-{current_year}.log"
    file_path = os.path.join("./logs", file_name)
    if not os.path.exists(file_path):
        open(file_path, 'w').close()
    return file_name


def logPrediction(response):
    logFileName = "./logs/"+getLogFileName(response["input"]["country"])
    # print(logFileName)
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
    file_path = os.path.join("./predictions",file_name)
    if not os.path.exists(file_path):
        open(file_path, 'w').close()

    try:
      oldData = pd.read_csv("./predictions/"+file_name)
      # print(oldData)
    except pd.errors.EmptyDataError:
      oldData = pd.DataFrame(columns=['startTime', 'percentRenewableForecast'])
    
    oldData["startTime"] =  pd.to_datetime(oldData['startTime']) # .dt.strftime('%Y%m%d%H%M')
    # print(oldData)
    newData = response["output"]
    newData["startTime"] =  pd.to_datetime(newData['startTime']) # .dt.strftime('%Y%m%d%H%M')
    # print(newData)
    mergedData = pd.concat([oldData,newData]).drop_duplicates(subset="startTime",keep='last')
    # print("merged file====")
    # print(mergedData)

    start_date, end_date = get_start_end_dates()
    # print(type(start_date))
    # Filter the merged DataFrame
    filteredData = mergedData[(mergedData['startTime'] >= start_date) & (mergedData['startTime'] <= end_date)]
    # print("filtered data")
    # print(filteredData)
    # filteredData['startTime'] = filteredData['startTime'].dt.strftime('%Y%m%d%H%M')
    # filteredData.to_csv(file_path, index=False, mode='w')
    mergedData.to_csv(file_path, index=False, mode='w')


def main():
  countryList = ml.model_get_available_country_list()
  for country in countryList:
    predictions = ml.model_run_latest(country)
    #print(predictions)
    savePredictionsToFile(predictions)
    logPrediction(predictions)


if __name__ == "__main__":
  main()