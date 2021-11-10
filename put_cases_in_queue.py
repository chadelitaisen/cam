import pyDOE
import numpy as np
np.random.seed(12344)
import boto3
import json
import random
import hashlib
import base64
import uuid
from io import BytesIO

from _aws_backend import DataBucketName, QueueURL, region
s3 = boto3.client('s3', region_name=region)
sqs = boto3.resource('sqs', region_name=region)
queue = sqs.Queue(QueueURL)

def put_JSON_on_s3(data, object_name):
    s3.upload_fileobj(BytesIO(json.dumps(data).encode()), DataBucketName, object_name)


prefixes = ["my_cases", "my_folder"]  # any number of folders is OK except zero
assert prefixes
prefix = "/".join(prefixes)


local_datafile = "prandtls_wedge.py"
remote_datafile = "public/" + local_datafile
s3.upload_file(local_datafile, DataBucketName, remote_datafile)

number_of_unknowns = 5

cube_files = ["cube_5_3.pkl", "cube_5_4.pkl"]
run_data = {}

for filename in cube_files:
    full_cube = np.load(filename)
    start, end = 0, len(full_cube)
    print(f"batch {step}: {start}-{end}")

    layers = number_of_unknowns
    raw_hyper_cube = full_cube[:, :layers]
    cohesion_hyper_cube = full_cube[:, layers:2*layers]

    for i in range(len(hyper_cube)):
        if i % 100 == 0:
            print("sending", i)
        case_id = case_ids[i]
        parameters = {
            "cohesion_array" : cohesion_hyper_cube[i].tolist(),
            "raw_parameters" : hyper_cube[i].tolist()}
        pfile = f"data/{prefix}/pfile-{case_id}.json"
        put_JSON_on_s3(parameters, pfile)
        data = {"case_id" : case_id,
                "base_file": remote_datafile,
                "parameter_file": pfile}
        body = json.dumps(data)
        mid = hashlib.sha256(body.encode()).hexdigest()
        reply = queue.send_message(MessageBody=body,
                                   MessageDeduplicationId=mid,
                                   MessageGroupId="main")
        _ = reply.get('MessageId')
        run_data[case_id] = {"parameters": parameters, "data": data}

put_JSON_on_s3(run_data, "all_runs.json")
with open("all_runs.json", "w") as f:
    json.dump(run_data, f)
