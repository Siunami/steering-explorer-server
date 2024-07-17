import boto3
import io
import json
import torch
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

s3 = boto3.client("s3")
BUCKET_NAME = "steering"  # Replace with your bucket name

# Near the top of your file, after imports
IS_PRODUCTION = os.environ.get("IS_PRODUCTION", "false").lower() == "true"


# def load_tensor_from_s3(key):
#     obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
#     buffer = io.BytesIO(obj["Body"].read())
#     return torch.load(buffer, map_location=torch.device("cpu"))


# def load_json_from_s3(key):
#     obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
#     return json.loads(obj["Body"].read().decode("utf-8"))


# # Load tensors from S3
# cos_sim_indices = load_tensor_from_s3("cosine_sim_indices.pt")
# cos_sim_values = load_tensor_from_s3("cosine_sim_values.pt")
# top_indices = load_tensor_from_s3("top_is_8000_16000.pt")
# top_values = load_tensor_from_s3("top_vs_8000_16000.pt")

# # Load JSON data from S3
# autointerp_data = load_json_from_s3("new_autointerp.json")
# data = load_json_from_s3("autointerp.json")


# def normalize_values(values):
#     # Ensure all values are non-negative
#     min_val = min(values)
#     shifted_values = [v - min_val for v in values]

#     # Calculate the sum of all shifted values
#     total = sum(shifted_values)

#     # If all values are the same (total is 0), return equal proportions
#     if total == 0:
#         return [1.0 / len(values)] * len(values)

#     # Normalize values so they sum to 1 while maintaining relative scales
#     return [v / total for v in shifted_values]


def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


@app.route("/", methods=["GET", "OPTIONS"])
def hello_world():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())
    return add_cors_headers(jsonify({"message": "Hello, World!"}))


# @app.route("/get_data", methods=["GET", "OPTIONS"])
# def get_data():
#     if request.method == "OPTIONS":
#         return add_cors_headers(make_response())

#     index = request.args.get("index", type=int)
#     print(index)

#     if index is None:
#         return add_cors_headers(jsonify({"error": "Missing parameters"}), 400)

#     indices = cos_sim_indices[index].tolist()
#     values = cos_sim_values[index].tolist()

#     return add_cors_headers(jsonify({"indices": indices, "values": values}))


@app.route("/get_data", methods=["GET", "OPTIONS"])
def get_data():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())

    print("All request args:", request.args)
    index = request.args.get("index", type=int, default=0)
    print("Received index:", index)

    if IS_PRODUCTION:
        api_url = f"https://siunami--example-get-started-webapp-get-data.modal.run/?index={index}"
    else:
        api_url = f"https://siunami--example-get-started-webapp-get-data-dev.modal.run/?index={index}"

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        return add_cors_headers(jsonify(data))
    else:
        return add_cors_headers(
            jsonify({"error": "Failed to fetch data from external API"}), 500
        )


@app.route("/get_top_effects", methods=["GET", "OPTIONS"])
def get_top_effects():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())

    feature = request.args.get("feature", type=int)
    print(feature)

    if IS_PRODUCTION:
        api_url = f"https://siunami--example-get-started-webapp-get-top-effects.modal.run/?feature={feature}"
    else:
        api_url = f"https://siunami--example-get-started-webapp-get-top-effects-dev.modal.run/?feature={feature}"

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        return add_cors_headers(jsonify(data))
    else:
        return add_cors_headers(
            jsonify({"error": "Failed to fetch data from external API"}), 500
        )


@app.route("/get_description", methods=["POST", "OPTIONS"])
def get_description():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())

    try:
        data = request.get_json()
        print("Received data:", data)

        if not data or "keys" not in data or not isinstance(data["keys"], list):
            return add_cors_headers(
                make_response(
                    jsonify(
                        {
                            "error": "Invalid request. Expected a JSON object with a 'keys' list."
                        }
                    ),
                    400,
                )
            )

        if IS_PRODUCTION:
            api_url = (
                "https://siunami--example-get-started-webapp-get-description.modal.run"
            )
        else:
            api_url = "https://siunami--example-get-started-webapp-get-description-dev.modal.run"

        print("Sending request to:", api_url)
        print(data)
        response = requests.post(api_url, json=data)
        print("External API response status:", response.status_code)

        if response.status_code == 200:
            return add_cors_headers(make_response(jsonify(response.json())))
        else:
            print("External API error response:", response.text)
            return add_cors_headers(
                make_response(
                    jsonify(
                        {
                            "error": f"External API returned status {response.status_code}"
                        }
                    ),
                    500,
                )
            )
    except Exception as e:
        print("Exception occurred:", str(e))
        return add_cors_headers(
            make_response(
                jsonify({"error": "An unexpected error occurred", "details": str(e)}),
                500,
            )
        )


@app.route("/search/<string:search_term>", methods=["GET", "OPTIONS"])
def search(search_term):
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())

    if not search_term:
        return add_cors_headers(jsonify({"error": "No search term provided"}), 400)

    if IS_PRODUCTION:
        api_url = f"https://siunami--example-get-started-webapp-search.modal.run/{search_term}"
    else:
        api_url = f"https://siunami--example-get-started-webapp-search-dev.modal.run/{search_term}"

    response = requests.get(api_url)

    if response.status_code == 200:
        return add_cors_headers(jsonify(response.json()))
    else:
        return add_cors_headers(
            jsonify({"error": "Failed to fetch data from external API"}), 500
        )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
