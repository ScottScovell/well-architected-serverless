import boto3
import os
import json
from boto3.dynamodb.conditions import Key

# Import AWS Lambda Powertools
from aws_lambda_powertools import Tracer, Logger, Metrics

tracer = Tracer()
logger = Logger()
metrics = Metrics()

@logger.inject_lambda_context
@metrics.log_metrics
@tracer.capture_lambda_handler
def lambda_handler(message, context):

    # Simple log statement
    logger.info('## Get Entity')

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

    # Log using object structure
    logger.info({
        "environment": environment,
        "region": region
    })

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

        results = table.query(
            KeyConditionExpression=Key('PK').eq(entity_id) & Key('SK').eq(entity_id)
        )

        # Trace DynamoDB results as custom metadata
        tracer.put_metadata(key="dynamodb_results", value=results)

        # return only the details attribute of the entity
        response = [ item['Details'] for item in results['Items'] ]

        return {
            'statusCode': 200,
            'headers': {},
            'body': json.dumps(response)
        }
    except Exception:
        logger.exception('Caught exception')
        raise