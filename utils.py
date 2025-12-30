import boto3
import json
import os

def get_aws_client(service_name):
    region_name = os.environ.get("AWS_REGION", "us-east-1")
    
    # Check if we should use LocalStack (default: True)
    use_localstack = os.environ.get("USE_LOCALSTACK", "true").lower() == "true"
    
    endpoint_url = None
    if use_localstack:
        endpoint_url = os.environ.get("AWS_ENDPOINT_URL")

    session = boto3.session.Session()
    return session.client(
        service_name=service_name,
        region_name=region_name,
        endpoint_url=endpoint_url
    )

def get_secret():
    secret_name = os.environ.get("SECRET_NAME")
    client = get_aws_client('secretsmanager')

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)
