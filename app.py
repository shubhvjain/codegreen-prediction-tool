from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from codecarbon import OfflineEmissionsTracker


def loadConfig():
  load_dotenv(".config")

app = Flask(__name__)

# Function to get current predictions based on country_code
def getCurrentPredictions(country_code):
    # Replace this with your actual prediction logic
    predictions = {
        "country": country_code,
        "prediction1": 42,
        "prediction2": 73
    }
    return predictions

@app.route('/get_predictions', methods=['POST'])
def get_predictions():
    try:
        data = request.json
        country_code = data.get("country_code")

        if country_code is None:
            return jsonify({"error": "Missing 'country_code' in request"}), 400

        predictions = getCurrentPredictions(country_code)
        return jsonify(predictions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    loadConfig()
    iso_code = os.getenv("CODECARBON_COUNTRY_ISO")
    tracker = OfflineEmissionsTracker(country_iso_code=iso_code,output_file="emission_server.csv")
    tracker.start()
    app.run(debug=False)
    tracker.stop()