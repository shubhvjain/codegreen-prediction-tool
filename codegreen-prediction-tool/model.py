# running prediction models 
import os

def runPredictionModel(modelName,input):
  print("This method runs a prediction model saved in the models folder")

def getLatestModelNameForCountry(country):
  print("returns the latest model name of a particular country")
  highestNumber = float('-inf')  # Start with a very low value
  highestNumberFile = None
  for fileName in os.listdir("./models"):
      if fileName.startswith(country + "_") and fileName.endswith(".h5"):
          fileNumber = int(fileName.split("_")[1].split(".")[0])
          if fileNumber > highestNumber:
              highestNumber = fileNumber
              highestNumberFile = fileName
  return highestNumberFile

def runLatestModelForCountry(country,input):  
  latestModelName =  getLatestModelNameForCountry(country)
  return runPredictionModel(latestModelName,input)
