import boto3
import os
import json
import uuid
from datetime import datetime

# Import AWS Lambda Powertools
from aws_lambda_powertools import Tracer, Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

tracer = Tracer()
logger = Logger()
metrics = Metrics()

@logger.inject_lambda_context
@metrics.log_metrics
@tracer.capture_lambda_handler
def lambda_handler(message, context):

    # Simple log statement
    logger.info('## Delete Entity')

    if ('pathParameters' not in message or
            message['httpMethod'] != 'DELETE'):

        # Simple log statement
        logger.info('No path params OR invalid http method')

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

        entity = {
            'PK': entity_id,
            'SK': entity_id
        }

        results = table.delete_item(
            Key=entity
        )

        # Trace DynamoDB results as custom metadata
        tracer.put_metadata(key="dynamodb_results", value=results)

        # Create metric for successful entity being added
        metrics.add_dimension(name="Region", value=region)
        metrics.add_metric(name="EntityDeleted", unit=MetricUnit.Count, value=1)

        return {
            'statusCode': 200,
            'headers': {},
            'body': json.dumps({'Message': 'Entity deleted'})
        }
    except Exception:
        logger.exception('Caught exception')
        raise      