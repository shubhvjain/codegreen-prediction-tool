from dotenv import load_dotenv
load_dotenv()

import entsoeAPI as e

print(e.entsoe_getDayAheadAggregatedGeneration({"country":"BE","start":"202308151000","end":"202308172100"}))
print(e.entsoe_getDayAheadGenerationForecastsWindSolar({"country":"BE","start":"202308151000","end":"202308172100"}))
print(e.getRenewableForecast({"country":"BE","start":"202308151000","end":"202308172100"}))