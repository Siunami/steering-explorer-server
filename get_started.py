import modal

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

    @modal.web_endpoint(docs=True)  # adds interactive documentation in the browser
    def get_data(self, index):
        # Convert index to integer
        index = int(index)
        # if request.method == "OPTIONS":
        #     return add_cors_headers(make_response())

        # index = request.args.get("index", type=int)
        # print(index)# Load tensors from S3

        indices = self.cos_sim_indices[index].tolist()
        values = self.cos_sim_values[index].tolist()

        return {"indices": indices, "values": values}

        if index is None:
            return add_cors_headers(jsonify({"error": "Missing parameters"}), 400)

        indices = cos_sim_indices[index].tolist()
        values = cos_sim_values[index].tolist()

        return add_cors_headers(jsonify({"indices": indices, "values": values}))


@app.function()
def square(x):
    print("This code is running on a remote worker!")
    # Convert x to an integer before squaring
    x = int(x)
    return x**2


@app.local_entrypoint()
def main():
    print("the square is", square.remote(42))
