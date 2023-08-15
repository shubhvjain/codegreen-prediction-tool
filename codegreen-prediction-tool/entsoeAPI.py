import pandas as pd
from datetime import datetime, timedelta
import time
from entsoe import EntsoePandasClient as entsoePandas
import os

import logging
logging.basicConfig(filename='entsoe.log', format='%(asctime)s - %(levelname)s - %(message)s',level="INFO")

DEBUG=True

def util_countIntervals(startDate, endDate, intervalMinutes):
    startDatetime = datetime.strptime(startDate, "%Y%m%d%H%M")
    endDatetime = datetime.strptime(endDate, "%Y%m%d%H%M")
    interval = timedelta(minutes=intervalMinutes)
    startBin = []
    endBin = []
    count = 0
    while startDatetime < endDatetime:
        a = startDatetime.strftime("%Y%m%d%H%M")
        count += 1
        startDatetime += interval
        b = startDatetime.strftime("%Y%m%d%H%M")
        startBin.append(a)
        endBin.append(b)
    return {"count":count,"startBin":startBin,"endBin":endBin}


def util_convertTo60MinInterval(rawData, start, end):
    duration = rawData["duration"]
    if duration == 60:
        """ If the duration is already 60, return data """
        return rawData["data"]
    elif duration < 60:
        """
        First, we determine the number of rows needed to combine in order to obtain data in a 60-minute format. 
        It is important to note that the rows are combined by taking the average of the row data, rather than the sum.
        """
        # determing how many rows need to be combined to get data in 60 min format. The rows are com
        groupingFactor = int(60/duration)
        oldData = rawData["data"]
        oldData["startTime"] = pd.to_datetime(oldData['startTime'])
        start_time = oldData["startTime"] .min()
        end_time = oldData["startTime"] .max()        
        durationMin=60
        expected_timestamps = pd.date_range(start=start_time, end=end_time, freq=f"{durationMin}T",tz='UTC')
        expected_timestamps = expected_timestamps.strftime('%Y%m%d%H%M')
        dataColToRemove = ['startTime']
        oldData = oldData.drop(dataColToRemove, axis=1)
        oldData['group_id'] = oldData.index // groupingFactor
        newGroupedData = oldData.groupby('group_id').mean()
        newGroupedData["startTime"] = expected_timestamps
        return newGroupedData


def getAPIToken():
  variable_name = "ENTSOE_TOKEN"
  value = os.environ.get(variable_name)
  if value is None:
    raise ValueError(f"The required environment variable '{variable_name}' is not set.")
  return value

def refineData(options,data1):
  durationMin = (data1.index[1] - data1.index[0]).total_seconds() / 60
  logging.info("  Row count : Fetched =  "+str(len(data1)))
  logging.info("  Duration : "+str(durationMin))

  start_time = data1.index.min()
  end_time = data1.index.max()
  expected_timestamps = pd.date_range(start=start_time, end=end_time, freq=f"{durationMin}T")
  expected_df = pd.DataFrame(index=expected_timestamps)
  missing_indices = expected_df.index.difference(data1.index)
  logging.info("  Missing values ("+str(len(missing_indices))+"):"+str(missing_indices))
  totalAverageValue = data1.mean().fillna(0).round().astype(int)
  for index in missing_indices:
    logging.info("    Missing value: "+str(index))
    rows_same_day = data1[ data1.index.date == index.date()]    
    if len(rows_same_day)>0 :
      avg_val = rows_same_day.mean().fillna(0).round().astype(int)
      avg_type = "average day value "+ str(rows_same_day.index[0].date())+" "
    else:
      avg_val = totalAverageValue
      avg_type = "whole data average "
    logging.info("      replaced with "+avg_type+" : "+' '.join(avg_val.astype(str)))
    new_row = pd.DataFrame([avg_val], columns=data1.columns, index=[index])
    data1 = pd.concat([data1, new_row]) 

    # prev_index = index - dur
    # next_index = index + dur
    # avg_val = (data1.loc[prev_index]+data1.loc[next_index])/2
    # logging.info("      previous value: " + ' '.join(data1.loc[prev_index].astype(str)))
    # logging.info("      previous value: " + ' '.join(data1.loc[next_index].astype(str)))
    # logging.info("      average value: " + ' '.join(avg_val.astype(str)))
    # new_row = pd.DataFrame([avg_val], columns=data1.columns, index=[index])
    # data1 = pd.concat([data1, new_row])
  data1['startTime'] = (data1.index.tz_convert('UTC')).strftime('%Y%m%d%H%M')
  data1.sort_index(inplace=True)
  

  return data1

def entsoe_getActualGenerationDataPerProductionType(options={"country": "", "start": "", "end": ""}):
    logging.info(options)
    startDay = pd.Timestamp(options["start"], tz='UTC')
    endDay = pd.Timestamp(options["end"], tz='UTC')
    client1 = entsoePandas(api_key=getAPIToken())
    data1 = client1.query_generation(options["country"], start=startDay, end=endDay,psr_type=None)

    columns_to_drop = [col for col in data1.columns if col[1] == 'Actual Consumption']
    data1 = data1.drop(columns=columns_to_drop)
    data1.columns = [(col[0] if isinstance(col, tuple) else col) for col in data1.columns]
    
    durationMin = (data1.index[1] - data1.index[0]).total_seconds() / 60
    
    refinedData  = refineData(options,data1)

    if DEBUG:   
      fileName= options["country"]+"-"+options["start"]+"-"+options["end"]+"-"+str(durationMin)+'-actual-raw'
      refinedData.to_csv("./test/"+fileName+".csv")
    
    refinedData = refinedData.reset_index(drop=True)
    return {"data":refinedData,"duration":durationMin}


def entsoe_getDayAheadAggregatedGeneration(options={"country": "", "start": "", "end": ""}):
    logging.info("DayAheadForecastsTotal")
    logging.info(options)
    client = entsoePandas(api_key=getAPIToken())
    data = client.query_generation_forecast(options["country"], start=pd.Timestamp(options["start"], tz='UTC'), end=pd.Timestamp(options["end"], tz='UTC'))
    if isinstance(data,pd.Series):
        data = data.to_frame(name="Actual Aggregated")
    durationMin = (data.index[1] - data.index[0]).total_seconds() / 60
    refinedData = refineData(options,data)
    newCol = {'Actual Aggregated': 'total'}
    refinedData.rename(columns=newCol, inplace=True)

    if DEBUG:   
      fileName= options["country"]+"-"+options["start"]+"-"+options["end"]+"-"+str(durationMin)+'-forecast-total-raw'
      refinedData.to_csv("./test/"+fileName+".csv")
    
    refinedData = refinedData.reset_index(drop=True)
    return {"data":refinedData,"duration":durationMin}


def entsoe_getDayAheadGenerationForecastsWindSolar(options={"country": "", "start": "", "end": ""}):
    logging.info("DayAheadForecastsWindSolar")
    logging.info(options)
    client = entsoePandas(api_key=getAPIToken())
    data = client.query_wind_and_solar_forecast(options["country"],  start=pd.Timestamp(options["start"], tz='UTC'), end=pd.Timestamp(options["end"], tz='UTC'))
    durationMin = (data.index[1] - data.index[0]).total_seconds() / 60
    refinedData1 = refineData(options,data) 
    validCols = ["Solar","Wind Offshore","Wind Onshore"]
    existingCol = []
    for col in validCols:
        if col in refinedData1.columns:
            existingCol.append(col)
    refinedData1["totalRenewable"] = refinedData1[existingCol].sum(axis=1)
    refinedData1 = refinedData1.reset_index(drop=True)

    if DEBUG:   
      fileName= options["country"]+"-"+options["start"]+"-"+options["end"]+"-"+str(durationMin)+'-forecast-wind-solar-raw'
      refinedData1.to_csv("./test/"+fileName+".csv")

    return {"data":refinedData1,"duration":durationMin}


def getActualRenewableValues(options={"country":"","start":"","end":"", "interval60":True}):
    totalRaw = entsoe_getActualGenerationDataPerProductionType(options)
    total = totalRaw["data"]
    duration = totalRaw["duration"]
    if options["interval60"] == True and totalRaw["duration"] != 60.0 :
      print("Data will to be converted to 60 min interval")
      table = util_convertTo60MinInterval(totalRaw,options["start"],options["end"])
      duration = 60
    else: 
      table = total 
    renewableSources = ["Geothermal","Hydro Pumped Storage","Hydro Run-of-river and poundage","Hydro Water Reservoir","Marine","Other renewable","Solar","Waste","Wind Offshore","Wind Onshore"]
    windSolarOnly = ["Solar","Wind Offshore","Wind Onshore"]
    nonRenewableSources = ["Biomass","Fossil Brown coal/Lignite","Fossil Coal-derived gas","Fossil Gas","Fossil Hard coal","Fossil Oil","Fossil Oil shale","Fossil Peal","Nuclear","Other"]
    allCols = table.columns.tolist()
    renPresent  = list(set(allCols).intersection(renewableSources))
    renPresentWS  = list(set(allCols).intersection(windSolarOnly))
    nonRenPresent = list(set(allCols).intersection(nonRenewableSources))
    table["renewableTotal"] = table[renPresent].sum(axis=1)
    table["renewableTotalWS"] = table[renPresentWS].sum(axis=1)
    table["nonRenewableTotal"] = table[nonRenPresent].sum(axis=1)
    table["total"] = table["nonRenewableTotal"] + table["renewableTotal"]
    table["percentRenewable"] = ( table["renewableTotal"] / table["total"] ) * 100
    table['percentRenewable'].fillna(0, inplace=True)
    table["percentRenewable"] = table["percentRenewable"].round().astype(int)
    table["percentRenewableWS"] = ( table["renewableTotalWS"] / table["total"] ) * 100
    table['percentRenewableWS'].fillna(0, inplace=True)
    table["percentRenewableWS"] = table["percentRenewableWS"].round().astype(int)
    return {"data":table,"duration":duration}


def getRenewableForecast(options={"country": "", "start": "", "end": "" }):
    # print(options)
    totalRaw = entsoe_getDayAheadAggregatedGeneration(options)
    if totalRaw["duration"] != 60 :
        total = util_convertTo60MinInterval(totalRaw,options["start"],options["end"])
    else :
        total = totalRaw["data"]
    
    windsolarRaw = entsoe_getDayAheadGenerationForecastsWindSolar(options)
    if  windsolarRaw["duration"] != 60 :
        windsolar = util_convertTo60MinInterval(windsolarRaw,options["start"],options["end"])
    else :
        windsolar = windsolarRaw["data"]   
  
    windsolar["total"] = total["total"]
    windsolar["percentRenewable"] = (windsolar['totalRenewable'] / windsolar['total']) * 100
    windsolar['percentRenewable'].fillna(0, inplace=True)
    windsolar["percentRenewable"] = windsolar["percentRenewable"].round().astype(int)
    return {"data":windsolar,"duration":60}
