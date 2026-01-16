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
    else:
        # Explicitly set to None to avoid boto3 picking up AWS_ENDPOINT_URL from env
        # when we want to use real AWS.
        endpoint_url = None

    session = boto3.session.Session()
    client_kwargs = {
        'service_name': service_name,
        'region_name': region_name,
    }
    
    # Only add endpoint_url if we are using LocalStack
    if use_localstack and endpoint_url:
        client_kwargs['endpoint_url'] = endpoint_url
        
    return session.client(**client_kwargs)

def get_secret():
    secret_name = os.environ.get("SECRET_NAME")
    client = get_aws_client('secretsmanager')

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)
