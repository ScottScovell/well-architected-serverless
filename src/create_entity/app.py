import boto3
import os
import json
import uuid
from datetime import datetime


def lambda_handler(message, context):

    if ('body' not in message or
            message['httpMethod'] != 'POST'):
        return {
            'statusCode': 400,
            'headers': {},
            'body': json.dumps({'msg': 'Bad Request'})
        }

    table_name = 'Entities'
    region = os.environ.get('REGION', 'us-east-1')
    environment = os.environ.get('AWS_SAM_LOCAL', 'false')

    print(environment)
    print(region)
    
    if os.environ.get('AWS_SAM_LOCAL', 'false') == 'true':
        ddb = boto3.resource(
            'dynamodb',
            endpoint_url='http://dynamodb:8000'
        )
    else:
        ddb = boto3.resource(
            'dynamodb',
            region_name=region
        )

    try:
        table = ddb.Table(table_name)
        body = json.loads(message['body'])
        entity_id = f'ent#{body["id"]}' if 'id' in body else f'ent#{str(uuid.uuid4())}'

        entity = {
            'PK': entity_id,
            'SK': entity_id,
            'Type': 'Entity',
            'Details': body
        }

        results = table.put_item(
            TableName=table_name,
            Item=entity
        )
        print(results)

        return {
            'statusCode': 201,
            'headers': {},
            'body': json.dumps({'Message': 'Entity created'})
        }
    except Exception as e:
        print('Caught exception: ', e)
        raise        