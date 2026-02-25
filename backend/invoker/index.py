import boto3
import json
import os
import uuid

client = boto3.client('bedrock-agentcore')

def handler(event, context):
    print("Received event:", json.dumps(event))
    
    agent_runtime_arn = os.environ.get('AGENT_RUNTIME_ARN')
    if not agent_runtime_arn:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'AGENT_RUNTIME_ARN environment variable not set'})
        }

    body = json.loads(event.get('body', '{}'))
    prompt = body.get('prompt')
    session_id = body.get('sessionId', str(uuid.uuid4()))
    
    try:
        payload = json.dumps({"prompt": prompt})
        
        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_runtime_arn,
            runtimeSessionId=session_id,
            payload=payload
        )
        
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
    except Exception as e:
        print(f"Error invoking agent: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
