import modal
from typing import Dict


# Define the secret
aws_secret = modal.Secret.from_name("my-aws-secret")

image = modal.Image.debian_slim().pip_install("torch", "boto3")

app = modal.App("example-get-started", image=image, secrets=[aws_secret])

# # @app.route("/get_data", methods=["GET", "OPTIONS"])
# @app.function(secrets=[aws_secret])
# @modal.web_endpoint(docs=True)  # adds interactive documentation in the browser
# def get_data(index):
#     # Convert index to integer
#     index = int(index)
#     # if request.method == "OPTIONS":
#     #     return add_cors_headers(make_response())

#     # index = request.args.get("index", type=int)
#     # print(index)# Load tensors from S3

#     indices = cos_sim_indices[index].tolist()
#     values = cos_sim_values[index].tolist()

#     return {"indices": indices, "values": values}

#     if index is None:
#         return add_cors_headers(jsonify({"error": "Missing parameters"}), 400)

#     indices = cos_sim_indices[index].tolist()
#     values = cos_sim_values[index].tolist()

#     return add_cors_headers(jsonify({"indices": indices, "values": values}))


@app.cls()
class WebApp:

    def add_cors_headers(response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @modal.enter()
    def startup(self):
        import boto3
        import io
        import json
        import torch

        self.s3 = boto3.client("s3")
        BUCKET_NAME = "steering"  # Replace with your bucket name

        def load_tensor_from_s3(key):
            obj = self.s3.get_object(Bucket=BUCKET_NAME, Key=key)
            buffer = io.BytesIO(obj["Body"].read())
            return torch.load(buffer, map_location=torch.device("cpu"))

        def load_json_from_s3(key):
            obj = self.s3.get_object(Bucket=BUCKET_NAME, Key=key)
            return json.loads(obj["Body"].read().decode("utf-8"))

        self.cos_sim_indices = load_tensor_from_s3("cosine_sim_indices.pt")
        self.cos_sim_values = load_tensor_from_s3("cosine_sim_values.pt")
        self.top_indices = load_tensor_from_s3("top_is_8000_16000.pt")
        self.top_values = load_tensor_from_s3("top_vs_8000_16000.pt")

        # Load JSON data from S3
        self.autointerp_data = load_json_from_s3("new_autointerp.json")
        self.data = load_json_from_s3("autointerp.json")

    @modal.web_endpoint(docs=True)  # adds interactive documentation in the browser
    def get_data(self, index):
        # Convert index to integer
        index = int(index)
        print(index)

        indices = self.cos_sim_indices[index].tolist()
        values = self.cos_sim_values[index].tolist()

        return {"indices": indices, "values": values}

    @modal.web_endpoint(docs=True)
    def get_top_effects(self, feature):
        # Convert feature to integer
        feature = int(feature)

        shifted_feature = feature - 8000

        if shifted_feature < 0 or shifted_feature >= 16000:
            return {"error": "Feature out of range"}

        indices = self.top_indices[shifted_feature].tolist()
        values = self.top_values[shifted_feature].tolist()

        return {"indices": indices, "values": values}

    @modal.web_endpoint(method="POST", docs=True)
    def get_description(self, json_data: Dict):
        print(json_data)
        keys = json_data.get("keys", [])
        print(keys)
        descriptions = {}

        for key in keys:
            description = self.autointerp_data.get(str(key))
            if description is not None:
                descriptions[key] = description
        print("descriptions")
        print(descriptions)

        return {"descriptions": descriptions}

    @modal.web_endpoint(docs=True)
    def search(self, search_term):
        results = []
        for item in self.data:
            if search_term.lower() in item[0].lower():
                results.append(item)
        return results


@app.function()
def square(x):
    print("This code is running on a remote worker!")
    # Convert x to an integer before squaring
    x = int(x)
    return x**2


@app.local_entrypoint()
def main():
    print("the square is", square.remote(42))
