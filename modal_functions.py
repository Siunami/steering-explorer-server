import modal
from typing import Dict


# Define the secret
aws_secret = modal.Secret.from_name("my-aws-secret")

image = modal.Image.debian_slim().pip_install("torch", "boto3")

app = modal.App("steering", image=image, secrets=[aws_secret])


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
        self.top_indices = load_tensor_from_s3("top_is.pt")
        self.top_values = load_tensor_from_s3("top_vs.pt")

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

        if feature < 0 or feature >= 16364:
            return {"error": "Feature out of range"}

        indices = self.top_indices[feature].tolist()
        values = self.top_values[feature].tolist()

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


@app.local_entrypoint()
def main():
    print("loaded")
