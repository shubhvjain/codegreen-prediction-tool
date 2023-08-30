"""
This file contains methods for interacting with the models stored in the "model" folder.
These methods include retrieving forecast data from the ENTSOE portal (which serves as 
input for prediction models) , running models, finding the latest models for a specific 
country, and obtaining a list of countries for which models are available.

The main method is `model_run_latest(country)`.
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import load_model

from . import entsoeAPI as en


def model_get_metaData(model):
    """Returns metadata for the selected model from the metadata.json file in the model folder"""
    with open("./models/metadata.json", "r") as file:
        data = json.load(file)
        obj = [o for o in data["models"] if o["name"] == model]
        if len(obj) == 1:
            return obj[0]
        else:
            raise Exception("Invalid model name")


def model_get_available_country_list():
    """Returns a list of country codes for which prediction models are available.
    All models are stored in the 'model' folder. There can be multiple models for one country.
    This method returns the unique names of all countries for which models exist.
    """
    country_names = set()
    folder_path = "./models"
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)) and filename.endswith(".h5"):
            country_name = filename.split('_')[0]
            country_names.add(country_name)
    return list(country_names)


def model_get_latest_name_for(country):
    """Returns the latest prediction model version number for a country.
    All models stored in the 'model' folder follow a common file naming convention: "countrycode_version".
    This method returns the value of the highest version available for the given country.
    """
    highestNumber = float('-inf')  # Start with a very low value
    highestNumberFile = None
    for fileName in os.listdir("./models"):
        if fileName.startswith(country + "_v") and fileName.endswith(".h5"):
            fileNumber = int(fileName.split("_")[1].split(".")[0][1:])
            if fileNumber > highestNumber:
                highestNumber = fileNumber
                highestNumberFile = fileName
    return highestNumberFile


def util_get_date_range():
    """Returns a dictionary with 2 keys: "start" and "end".
    The "start" date is 5 days before the current date, and the "end" date is 2 days after the current date.
    Both dates are in the format YYYYMMDDhhmm, with the "hhmm" part set as "0000".
    """
    # Get today's date
    today_utc = datetime.now()
    # Calculate start and end dates
    start_date = (today_utc - timedelta(days=5)).replace(hour=0,
                                                         minute=0, second=0, microsecond=0)
    end_date = (today_utc + timedelta(days=2)).replace(hour=0,
                                                       minute=0, second=0, microsecond=0)
    # Format dates in "YYYYMMDDhhmm" format
    start_date_str = start_date.strftime('%Y%m%d%H%M')
    end_date_str = end_date.strftime('%Y%m%d%H%M')
    date_range = {
        "start": start_date_str,
        "end": end_date_str
    }
    return date_range


def ENTSOE_get_percent_renewable_forecasts(country, input_sequence):
    ''' Returns a pandas DataFrame of the hourly forecasted percentage of renewable energy collected from the ENTSOE portal for a 
    specified country over the last n hours.
    The value of n is determined by the input_sequence provided.
    The output from this method serves as input for running the model.
    The start time corresponds to 5 days prior to the current date, and the end time corresponds to 2 days after the current date.
    '''
    input = util_get_date_range()
    input["country"] = country
    data = en.getRenewableForecast(input)
    last_n_rows = data["data"].tail(input_sequence)
    return last_n_rows


def model_run(model_name, input):
    """Generates the next 48-hour prediction values by executing the provided model using the corresponding input data.
    Model name is the string
    input is the pandas dataframe 
    """
    seq_length = len(input)
    date = input[['startTime']].copy()
    # Convert 'startTime' column to datetime
    date['startTime'] = pd.to_datetime(date['startTime'])
    # Get the last date value
    last_date = date.iloc[-1]['startTime']
    # Calculate the next hour
    next_hour = last_date + timedelta(hours=1)
    # Create a range of 48 hours starting from the next hour
    next_48_hours = pd.date_range(next_hour, periods=48, freq='H')
    # Create a DataFrame with the next 48 hours
    next_48_hours_df = pd.DataFrame(
        {'startTime': next_48_hours.strftime('%Y%m%d%H%M')})
    # print(next_48_hours_df)
    # Construct the model filename by appending '.h5' to the model name
    model_filename = "./models/"+model_name
    # Load the specified model
    lstm = load_model(model_filename, compile=False)
    scaler = StandardScaler()
    percent_renewable = input['percentRenewable']
    forecast_values_total = []
    prev_values_total = percent_renewable.values.flatten()
    for _ in range(48):
        scaled_prev_values_total = scaler.fit_transform(
            prev_values_total.reshape(-1, 1))
        x_pred_total = scaled_prev_values_total[-(
            seq_length-1):].reshape(1, (seq_length-1), 1)
        # Make the prediction using the loaded model
        predicted_value_total = lstm.predict(x_pred_total, verbose=0)
        # Inverse transform the predicted value
        predicted_value_total = scaler.inverse_transform(predicted_value_total)
        forecast_values_total.append(predicted_value_total[0][0])
        prev_values_total = np.append(prev_values_total, predicted_value_total)
        prev_values_total = prev_values_total[1:]
    # Create a DataFrame
    forecast_df = pd.DataFrame(
        {'startTime': next_48_hours_df['startTime'], 'percentRenewableForecast': forecast_values_total})
    forecast_df["percentRenewableForecast"] = forecast_df["percentRenewableForecast"].round(
    ).astype(int)
    forecast_df['percentRenewableForecast'] = forecast_df['percentRenewableForecast'].apply(
        lambda x: 0 if x <= 0 else x)
    return forecast_df


def model_run_latest(country) -> dict:
    """ Returns  predictions by running the latest version of model available for the input country
    :param country : 2 letter country code
    :type country : str
    :return Dictionary { "input": { "country":"", "model":"", "start":"", "end":"",  "percentRenewable":[],  } , "output": <pandas dataframe> }
    """
    # get the name of the latest model  and its metadata
    model_name = model_get_latest_name_for(country)
    model_meta = model_get_metaData(model_name)
    input_sequence = model_meta["input_sequence"]
    country = model_meta["country"]
    # get input for the model : last n values of percent renewable 
    input_data = ENTSOE_get_percent_renewable_forecasts(
        country, input_sequence)
    input_percentage = input_data["percentRenewable"].tolist()
    input_start = input_data.iloc[0]["startTime"]
    input_end = input_data.iloc[-1]["startTime"]
    # run the model 
    output = model_run(model_name, input_data)
    return {
        "input": {
            "country": country,
            "model": model_name,
            "percentRenewable": input_percentage,
            "start": input_start,
            "end": input_end
        },
        "output": output
    }
