import boto3
from botocore.exceptions import ClientError
import json
import config

import logging
logger = logging.getLogger(__name__)

def create_runtime():
    try:
        BEDROCK_RUNTIME = boto3.client(
            service_name='bedrock-runtime', 
            region_name=config.AWS_BEDROCK_REGION,
            aws_access_key_id=config.AWS_BEDROCK_ACCESS_KEY, 
            aws_secret_access_key=config.AWS_BEDROCK_SECRET_KEY
        )
    except Exception:
        BEDROCK_RUNTIME = None
    
    return BEDROCK_RUNTIME

def _create_claude_payload(prompt: str):
    return json.dumps({ 
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 64000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    })

# AWS bedrock helper functions
def call_bedrock(prompt: str, br_runtime):
    try:
        response = br_runtime.invoke_model(
            body=_create_claude_payload(prompt), 
            modelId=config.AWS_BEDROCK_MODELID, 
            accept='application/json', 
            contentType='application/json'
        )

        body = json.loads(response.get('body').read().decode('utf-8'))
        answer = body.get("content",[])[0]['text']
    except ClientError as e:
        logger.error(f'Could not invoke Claude due to {e.response["Error"]["Code"]} and {e.response["Error"]["Message"]} when calling with {prompt}')
        answer = "Error calling Claude."

    return answer

def read_file(file):
    with open(file, 'r') as f:
        return f.read()

def strip_bedrock_output(output):
    output = output.replace("    ", "")
    output = output.replace("\n", "")
    output = output.strip()
    return json.loads(output)

def add_openapi_spec_details(paths):
    for idx, path in enumerate(paths):
        for method in paths[path]:
            paths[path][method]["responses"] = {
                "200": {
                    "description": "Successful response"
                }
            }
    
    return paths

def chunk_code(code, chunk_size):
    return [code[i:i+chunk_size] for i in range(0, len(code), chunk_size)]