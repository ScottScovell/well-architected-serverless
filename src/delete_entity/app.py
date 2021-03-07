import boto3
import os
import json
import uuid
from datetime import datetime


def lambda_handler(message, context):

    if ('pathParameters' not in message or
            message['httpMethod'] != 'DELETE'):
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
        entity_id = f'ent#{message["pathParameters"]["id"]}'

        entity = {
            'PK': entity_id,
            'SK': entity_id
        }

        results = table.delete_item(
            Key=entity
        )
        print(results)

        return {
            'statusCode': 200,
            'headers': {},
            'body': json.dumps({'Message': 'Entity deleted'})
        }
    except Exception as e:
        print('Caught exception: ', e)
        raise        