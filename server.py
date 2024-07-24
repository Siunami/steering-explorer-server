import boto3
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

print(IS_PRODUCTION)

BASE_URL = "https://siunami--steering-webapp-get-data.modal.run"
BASE_URL_DEV = "https://siunami--steering-webapp-get-data-dev.modal.run"


def add_cors_headers(response, status_code=200):
    if isinstance(response, dict):
        response = jsonify(response)
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    response.status_code = status_code
    return response


@app.route("/", methods=["GET", "OPTIONS"])
def hello_world():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())
    return add_cors_headers(jsonify({"message": "Hello, World!"}))


@app.route("/get_cos_sim", methods=["GET", "OPTIONS"])
def get_cos_sim():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())

    print("All request args:", request.args)
    index = request.args.get("index", type=int, default=0)
    print("Received index:", index)

    if IS_PRODUCTION:
        api_url = (
            f"https://siunami--steering-webapp-get-cos-sim.modal.run/?index={index}"
        )
    else:
        api_url = (
            f"https://siunami--steering-webapp-get-cos-sim-dev.modal.run/?index={index}"
        )

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
        api_url = f"https://siunami--steering-webapp-get-top-effects.modal.run/?feature={feature}"
    else:
        api_url = f"https://siunami--steering-webapp-get-top-effects-dev.modal.run/?feature={feature}"

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        return add_cors_headers(jsonify(data))
    else:
        return add_cors_headers(
            jsonify({"error": "Failed to fetch data from external API"}), 500
        )


@app.route("/get_top_actions", methods=["GET", "OPTIONS"])
def get_top_actions():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())

    feature = request.args.get("feature", type=int)
    print(feature)

    if IS_PRODUCTION:
        api_url = f"https://siunami--steering-webapp-get-top-actions.modal.run/?feature={feature}"
    else:
        api_url = f"https://siunami--steering-webapp-get-top-actions-dev.modal.run/?feature={feature}"

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        return add_cors_headers(jsonify(data))
    else:
        return add_cors_headers(
            jsonify({"error": "Failed to fetch data from external API"}), 500
        )


@app.route("/get_co_occurring_effects", methods=["GET", "OPTIONS"])
def get_co_occurring_effects():
    if request.method == "OPTIONS":
        return add_cors_headers({})

    feature = request.args.get("feature", type=int)
    print(f"Getting co-occurring effects for feature: {feature}")

    if IS_PRODUCTION:
        api_url = f"https://siunami--steering-webapp-get-co-occuring-effects-dev.modal.run/?feature={feature}"
    else:
        api_url = f"https://siunami--steering-webapp-get-co-occuring-effects-dev.modal.run/?feature={feature}"

    print(api_url)

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        return add_cors_headers(data)
    else:
        return add_cors_headers(
            {"error": "Failed to fetch co-occurring effects data from external API"},
            500,
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
            api_url = f"https://siunami--steering-webapp-get-description.modal.run"
        else:
            api_url = f"https://siunami--steering-webapp-get-description-dev.modal.run"

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
        api_url = f"https://siunami--steering-webapp-search.modal.run/?search_term={search_term}"
    else:
        api_url = f"https://siunami--steering-webapp-search-dev.modal.run/?search_term={search_term}"

    response = requests.get(api_url)

    if response.status_code == 200:
        return add_cors_headers(jsonify(response.json()))
    else:
        return add_cors_headers(
            jsonify({"error": "Failed to fetch data from external API"}), 500
        )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
