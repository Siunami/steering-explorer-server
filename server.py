import torch
from flask import Flask, jsonify, request, make_response
import json
from flask_cors import CORS  # Add this import

app = Flask(__name__)
CORS(app)  # Allow all origins for all routes

# Load all tensors
try:
    cos_sim_indices = torch.load(
        "cosine_sim_indices.pt", map_location=torch.device("cpu")
    )
    cos_sim_values = torch.load(
        "cosine_sim_values.pt", map_location=torch.device("cpu")
    )
except Exception as e:
    print(f"Error loading PyTorch files: {e}")
    exit(1)

# Load tensors from load_effects.py
try:
    top_indices = torch.load("top_is_8000_16000.pt", map_location=torch.device("cpu"))
    top_values = torch.load("top_vs_8000_16000.pt", map_location=torch.device("cpu"))
except Exception as e:
    print(f"Error loading PyTorch files for top effects: {e}")
    exit(1)

# Load the new_autointerp.json file
with open("new_autointerp.json", "r") as f:
    autointerp_data = json.load(f)


def normalize_values(values):
    # Ensure all values are non-negative
    min_val = min(values)
    shifted_values = [v - min_val for v in values]

    # Calculate the sum of all shifted values
    total = sum(shifted_values)

    # If all values are the same (total is 0), return equal proportions
    if total == 0:
        return [1.0 / len(values)] * len(values)

    # Normalize values so they sum to 1 while maintaining relative scales
    return [v / total for v in shifted_values]


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


@app.route("/get_data", methods=["GET", "OPTIONS"])
def get_data():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())

    index = request.args.get("index", type=int)
    print(index)

    if index is None:
        return add_cors_headers(jsonify({"error": "Missing parameters"}), 400)

    indices = cos_sim_indices[index].tolist()
    values = cos_sim_values[index].tolist()

    return add_cors_headers(jsonify({"indices": indices, "values": values}))


@app.route("/get_top_effects", methods=["GET", "OPTIONS"])
def get_top_effects():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())

    feature = request.args.get("feature", type=int)
    print(feature)

    if feature is None:
        return add_cors_headers(jsonify({"error": "Missing feature parameter"}), 400)

    shifted_feature = feature - 8000

    if shifted_feature < 0 or shifted_feature >= 16000:
        return add_cors_headers(jsonify({"error": "Feature out of range"}), 400)

    indices = top_indices[shifted_feature].tolist()
    values = top_values[shifted_feature].tolist()

    return add_cors_headers(jsonify({"indices": indices, "values": values}))


@app.route("/get_description", methods=["POST", "OPTIONS"])
def get_description():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())

    data = request.get_json()

    if not data or "keys" not in data or not isinstance(data["keys"], list):
        return add_cors_headers(
            jsonify(
                {"error": "Invalid request. Expected a JSON object with a 'keys' list."}
            ),
            400,
        )

    keys = data["keys"]
    descriptions = {}

    for key in keys:
        description = autointerp_data.get(str(key))
        if description is not None:
            descriptions[key] = description

    return add_cors_headers(jsonify({"descriptions": descriptions}))


# Load the JSON data from the file
with open("./autointerp.json", "r") as file:
    data = json.load(file)


def search_features(search_term):
    results = []
    for i, item in enumerate(data):
        if search_term.lower() in item[0].lower():
            results.append(item)
    return results


@app.route("/search/<string:search_term>", methods=["GET", "OPTIONS"])
def search(search_term):
    if request.method == "OPTIONS":
        return add_cors_headers(make_response())

    if not search_term:
        response = add_cors_headers(jsonify({"error": "No search term provided"}), 400)
    else:
        results = search_features(search_term)
        response = add_cors_headers(jsonify(results))

    print(response)

    return response


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
