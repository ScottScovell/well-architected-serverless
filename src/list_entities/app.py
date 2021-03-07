import boto3
import os
import json

def lambda_handler(message, context):

    if ('pathParameters' not in message or
            message['httpMethod'] != 'GET'):
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

        results = table.scan()
        print(results)

        # return only the details attribute of the entity
        response = [ item['Details'] for item in results['Items'] ]

        return {
            'statusCode': 200,
            'headers': {},
            'body': json.dumps(response)
        }
    except Exception as e:
        print('Caught exception: ', e)
        raise
