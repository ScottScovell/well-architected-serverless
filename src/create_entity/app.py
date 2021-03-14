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
    logger.info('## Create Entity')

    if ('body' not in message or
            message['httpMethod'] != 'POST'):

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

        # Trace DynamoDB results as custom metadata
        tracer.put_metadata(key="dynamodb_results", value=results)

        # Create metric for successful entity being added
        metrics.add_dimension(name="Region", value=region)
        metrics.add_metric(name="EntityCreated", unit=MetricUnit.Count, value=1)

        return {
            'statusCode': 201,
            'headers': {},
            'body': json.dumps({'Message': 'Entity created'})
        }
    except Exception:
        logger.exception('Caught exception')
        raise      