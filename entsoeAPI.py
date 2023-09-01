import pandas as pd
from datetime import datetime, timedelta
import time
from entsoe import EntsoePandasClient as entsoePandas
import os


def get_API_token() -> str:
    """Returns the token required to access the ENTSOE API. The token is stored as environment variable `ENTSOE_TOKEN`"""
    variable_name = "ENTSOE_TOKEN"
    value = os.environ.get(variable_name)
    if value is None:
        raise ValueError(
            f"The required environment variable '{variable_name}' is not set.")
    return value


def refine_data(options, data1):
    """Returns a refined version of the dataframe. 
    The Refining process involves finding missing values and substituting them with average values. 
    Additionally, a new column `startTimeUTC` is appended to the dataframe representing the start time in UTC  
    :param options 
    :param data1 : the dataframe that has to be refined. Assuming it has a datetime index in local time zone with country info
    :returns {"data":Refined data frame, "refine_logs":["list of refinements made"]}
    """

    # calculate the duration of the time series by finding the difference between the
    # first and the second index (which is of the type `datatime``) and convert this into minutes
    durationMin = (data1.index[1] - data1.index[0]).total_seconds() / 60
    # initializing the log list
    refine_logs = []
    refine_logs.append("Row count : Fetched =  " +
                       str(len(data1)) + ", duration : "+str(durationMin))
    """
    Determining the list of records that are absent in the time series by initially creating a set containing all 
    the expected timestamps within the start and end time range. Then, we calculate the difference between 
    this set and the timestamps present in the actual DataFrame.
    """
    start_time = data1.index.min()
    end_time = data1.index.max()
    expected_timestamps = pd.date_range(
        start=start_time, end=end_time, freq=f"{durationMin}T")
    expected_df = pd.DataFrame(index=expected_timestamps)
    missing_indices = expected_df.index.difference(data1.index)
    """ Next, we fill in the missing values. 
    For each absent timestamp, we examine if the entries for the same day exists. 
    If they do, we use the day average for each column in the Dataframe. 
    Else, we use the average of the entire data
    """
    totalAverageValue = data1.mean().fillna(0).round().astype(int)
    for index in missing_indices:
        rows_same_day = data1[data1.index.date == index.date()]
        if len(rows_same_day) > 0:
            avg_val = rows_same_day.mean().fillna(0).round().astype(int)
            avg_type = "average day value " + \
                str(rows_same_day.index[0].date())+" "
        else:
            avg_val = totalAverageValue
            avg_type = "whole data average "
        refine_logs.append("Missing value: "+str(index) + "      replaced with " +
                           avg_type + " : "+' '.join(avg_val.astype(str)))
        new_row = pd.DataFrame([avg_val], columns=data1.columns, index=[index])
        data1 = pd.concat([data1, new_row])
        # prev_index = index - dur
        # next_index = index + dur
        # avg_val = (data1.loc[prev_index]+data1.loc[next_index])/2
        # new_row = pd.DataFrame([avg_val], columns=data1.columns, index=[index])
        # data1 = pd.concat([data1, new_row])

    """ Currently, the datatime index is set in the time zone of the data's country of origin. 
    We convert it into UTC and add it as a new column named 'startTimeUTC' in the 'YYYYMMDDhhmm' format.
    """
    data1['startTimeUTC'] = (data1.index.tz_convert('UTC')).strftime('%Y%m%d%H%M')
    # data1['startTimeLocal'] = (data1.index).strftime('%Y%m%d%H%M')
    # since missing values are concatenated to the dataframe, it is also sorted based on the datetime index
    data1.sort_index(inplace=True)
    return {"data": data1, "refine_logs": refine_logs}


def entsoe_get_actual_generation(options={"country": "", "start": "", "end": ""}):
    """Fetches the aggregated actual generation per production type data (16.1.B&C) for the given country within the given start and end date
    params: options = {country (2 letter country code),start,end} . Both the dates are in the YYYYMMDDhhmm format and the local time zone
    returns : {"data":pd.DataFrame, "duration":duration (in min) of the time series data, "refine_logs":"notes on refinements made" }
    """
    client1 = entsoePandas(api_key=get_API_token())
    data1 = client1.query_generation(
        options["country"],
        start=pd.Timestamp(options["start"], tz='UTC'),
        end=pd.Timestamp(options["end"], tz='UTC'),
        psr_type=None)
    # drop columns with actual consumption values (we want actual aggregated generation values)
    columns_to_drop = [
        col for col in data1.columns if col[1] == 'Actual Consumption']
    data1 = data1.drop(columns=columns_to_drop)
    # If certain column names are in the format of a tuple like (energy_type, 'Actual Aggregated'),
    # these column names are transformed into strings using the value of energy_type.
    data1.columns = [(col[0] if isinstance(col, tuple) else col)
                     for col in data1.columns]
    # refine the dataframe. see the refine method
    data2 = refine_data(options, data1)
    refined_data = data2["data"]
    refined_data = refined_data.reset_index(drop=True)
    # finding the duration of the time series data
    durationMin = (data1.index[1] - data1.index[0]).total_seconds() / 60
    return {"data": refined_data, "duration": durationMin, "refine_logs": data2["refine_logs"]}


def entsoe_get_total_forecast(options={"country": "", "start": "", "end": ""}):
    """Fetches the aggregated day ahead total generation forecast data (14.1.C) for the given country within the given start and end date
    params: options = {country (2 letter country code),start,end} . Both the dates are in the YYYYMMDDhhmm format and the local time zone
    returns : {"data":pd.DataFrame, "duration":duration (in min) of the time series data, "refine_logs":"notes on refinements made" }
    """
    client = entsoePandas(api_key=get_API_token())
    data = client.query_generation_forecast(
        options["country"],
        start=pd.Timestamp(options["start"], tz='UTC'),
        end=pd.Timestamp(options["end"], tz='UTC'))
    # if the data is a series instead of a dataframe, it will be converted to a dataframe
    if isinstance(data, pd.Series):
        data = data.to_frame(name="Actual Aggregated")
    durationMin = (data.index[1] - data.index[0]).total_seconds() / 60
    # refining the data
    data2 = refine_data(options, data)
    refined_data = data2["data"]
    # rename the single column
    newCol = {'Actual Aggregated': 'total'}
    refined_data.rename(columns=newCol, inplace=True)
    refined_data = refined_data.reset_index(drop=True)
    return {"data": refined_data, "duration": durationMin, "refine_logs": data2["refine_logs"]}



def entsoe_get_wind_solar_forecast(options={"country": "", "start": "", "end": ""}):
    """Fetches the aggregated day ahead wind and solar generation forecast data  (14.1.D) for the given country within the given start and end date
    params: options = {country (2 letter country code),start,end} . Both the dates are in the YYYYMMDDhhmm format and the local time zone
    returns : {"data":pd.DataFrame, "duration":duration (in min) of the time series data, "refine_logs":"notes on refinements made" }
    """
    client = entsoePandas(api_key=get_API_token())
    data = client.query_wind_and_solar_forecast(
        options["country"],
        start=pd.Timestamp(options["start"], tz='UTC'),
        end=pd.Timestamp(options["end"], tz='UTC'))
    durationMin = (data.index[1] - data.index[0]).total_seconds() / 60
    # refining the data
    data2 = refine_data(options, data)
    refined_data = data2["data"]
    # calculating the total renewable consumption value
    validCols = ["Solar", "Wind Offshore", "Wind Onshore"]
    existingCol = []
    for col in validCols:
        if col in refined_data.columns:
            existingCol.append(col)
    refined_data["totalRenewable"] = refined_data[existingCol].sum(axis=1)
    refined_data = refined_data.reset_index(drop=True)
    return {"data": refined_data, "duration": durationMin, "refine_logs": data2["refine_logs"]}


def convert_to_60min_interval(rawData):
    """Given the rawData obtained from the ENTSOE API methods, this function converts the DataFrame into 
    60-minute time intervals by aggregating data from multiple rows. """
    duration = rawData["duration"]
    if duration == 60:
        """ If the duration is already 60, return data """
        return rawData["data"]
    elif duration < 60:
        """
        First, we determine the number of rows needed to combine in order to obtain data in a 60-minute format. 
        It is important to note that the rows are combined by taking the average of the row data, rather than the sum.
        """
        # determining how many rows need to be combined to get data in 60 min format.
        groupingFactor = int(60/duration)
        oldData = rawData["data"]
        oldData["startTimeUTC"] = pd.to_datetime(oldData['startTimeUTC'])
        start_time = oldData["startTimeUTC"] .min()
        end_time = oldData["startTimeUTC"] .max()
        durationMin = 60
        # removing the old timestamps (which are not 60 mins apart)
        dataColToRemove = ['startTimeUTC']
        # dataColToRemove = ['startTimeUTC','startTimeLocal']
        oldData = oldData.drop(dataColToRemove, axis=1)

        oldData['group_id'] = oldData.index // groupingFactor
        newGroupedData = oldData.groupby('group_id').mean()
        # new timestamps which are 60 min apart 
        new_timestamps = pd.date_range(
            start=start_time, end=end_time, freq=f"{durationMin}T", tz='UTC')
        new_timestamps = new_timestamps.strftime('%Y%m%d%H%M')
        newGroupedData["startTimeUTC"] = new_timestamps
        return newGroupedData


def get_actual_percent_renewable(country, start, end, interval60=False) -> pd.DataFrame:
    """Returns time series data containing the percentage of energy generated from renewable sources for the specified country within the selected time period. 
    The data is sourced from the ENTSOE APIs and subsequently refined. 
    To obtain data in 60-minute intervals (if not already available), set 'interval60' to True
    """
    options = {"country": country, "start": start,
               "end": end, "interval60": interval60}
    # get actual generation data per production type and convert it into 60 min interval if required
    totalRaw = entsoe_get_actual_generation(options)
    total = totalRaw["data"]
    duration = totalRaw["duration"]
    if options["interval60"] == True and totalRaw["duration"] != 60.0:
        table = convert_to_60min_interval(totalRaw)
        duration = 60
    else:
        table = total
    # print("actual total")
    # print(totalRaw["refine_logs"])
    # finding the percent renewable
    renewableSources = ["Geothermal", "Hydro Pumped Storage", "Hydro Run-of-river and poundage",
                        "Hydro Water Reservoir", "Marine", "Other renewable", "Solar", "Waste", "Wind Offshore", "Wind Onshore"]
    windSolarOnly = ["Solar", "Wind Offshore", "Wind Onshore"]
    nonRenewableSources = ["Biomass", "Fossil Brown coal/Lignite", "Fossil Coal-derived gas", "Fossil Gas",
                           "Fossil Hard coal", "Fossil Oil", "Fossil Oil shale", "Fossil Peal", "Nuclear", "Other"]
    allCols = table.columns.tolist()
    # find out which columns are present in the data out of all the possible columns in both the categories
    renPresent = list(set(allCols).intersection(renewableSources))
    renPresentWS = list(set(allCols).intersection(windSolarOnly))
    nonRenPresent = list(set(allCols).intersection(nonRenewableSources))
    # find total renewable, total non renewable and total energy values
    table["renewableTotal"] = table[renPresent].sum(axis=1)
    table["renewableTotalWS"] = table[renPresentWS].sum(axis=1)
    table["nonRenewableTotal"] = table[nonRenPresent].sum(axis=1)
    table["total"] = table["nonRenewableTotal"] + table["renewableTotal"]
    # calculate percent renewable
    table["percentRenewable"] = (
        table["renewableTotal"] / table["total"]) * 100
    # refine percentage values : replacing missing values with 0 and converting to integer
    table['percentRenewable'].fillna(0, inplace=True)
    table["percentRenewable"] = table["percentRenewable"].round().astype(int)
    table["percentRenewableWS"] = (
        table["renewableTotalWS"] / table["total"]) * 100
    table['percentRenewableWS'].fillna(0, inplace=True)
    table["percentRenewableWS"] = table["percentRenewableWS"].round().astype(int)
    return table


def get_forecast_percent_renewable(country, start, end) -> pd.DataFrame:
    """Returns time series data comprising the forecast of the percentage of energy generated from 
    renewable sources (specifically, wind and solar) for the specified country within the selected time period. 
    The data source is the  ENTSOE APIs and involves combining data from 2 APIs : total forecast, wind and solar forecast.
    To obtain data in 60-minute intervals (if not already available), set 'interval60' to True"""
    options = {"country": country, "start": start,
               "end": end}
    totalRaw = entsoe_get_total_forecast(options)
    if totalRaw["duration"] != 60:
        total = convert_to_60min_interval(totalRaw)
    else:
        total = totalRaw["data"]
    windsolarRaw = entsoe_get_wind_solar_forecast(options)
    if windsolarRaw["duration"] != 60:
        windsolar = convert_to_60min_interval(windsolarRaw)
    else:
        windsolar = windsolarRaw["data"]
    # print("wind solar forecast raw"); print(windsolarRaw["refine_logs"])
    # print("total forecast raw"); print(totalRaw["refine_logs"])
    windsolar["total"] = total["total"]
    windsolar["percentRenewable"] = (
        windsolar['totalRenewable'] / windsolar['total']) * 100
    windsolar['percentRenewable'].fillna(0, inplace=True)
    windsolar["percentRenewable"] = windsolar["percentRenewable"].round().astype(int)
    return windsolar
