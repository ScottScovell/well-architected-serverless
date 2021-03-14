# Part 2 - AWS Lambda PowerTools for Python

The AWS Lambda PowerTools for Python is an open source framework library that assists building well-architected serverless applications. It implements a number of observability best practices across the three core observability pillars.

The Logger class provides a custom Python logger that outputs structured JSON. It allows you to pass in strings or more complex objects, and will take care of serializing the log output. Common use cases—such as logging the Lambda event payload and capturing cold start information—are handled for you, including appending custom keys to the logger at anytime.

The Metrics class makes collecting custom metrics from your application simple, without the need to make synchronous requests to external systems. This functionality is powered by Amazon CloudWatch Embedded Metric Format (EMF), which allows for capturing metrics asynchronously. 

The Tracer class provides a simple way to send traces from functions to AWS X-Ray to provide visibility into function calls, interactions with other AWS services, or external HTTP requests. Annotations easily can be added to traces to allow filtering traces based on key information.

In this post, we'll take a sample serverless application and implement a number of observability best practices using the AWS Lambda PowerTools.

## Get the sample basic lambda service application

Clone the following GitHub repository

```bash
git clone https://github.com/ScottScovell/well-architected-serverless.git
```

You can either implement the changes below as you walk through, or checkout the completed feature branch part-2/aws-lambda-powertools review the code and deploy into your AWS account.

## Setting up AWS Lambda PowerTools for Python

First we need to add the AWS Lambda PowerTool dependencies to the `requirements.txt` file for each of our functions.

```
boto3
aws-lambda-powertools
```

Next we add the imports for the Tracer, Logger, and Metrics components to our Lambda function.

```python
# Import AWS Lambda Powertools
from aws_lambda_powertools import Tracer, Logger, Metrics

tracer = Tracer()
logger = Logger()
metrics = Metrics()
```

We can add decorators to our handler function to enrich the capabilities of these components. For example, to inject the event context into our log statements, we can use the following logger decorator

```python
@logger.inject_lambda_context
def lambda_handler(message, context):
```

This configures AWS Lambda Power Tools to capture key fields from the Lambda context as well as Lambda runtime information such as cold starts, memory size etc.

Should we wish to log the incoming event as well, we can add the following parameter to the inject_lambda_context. 

```python
@logger.inject_lambda_context(log_event=True)
def lambda_handler(message, context):
```

We can also do this via an environment variable,  POWERTOOLS_LOGGER_LOG_EVENT, as shown in the next step.

Lets add the decorator for metrics next:

```python
@logger.inject_lambda_context
@metrics.log_metrics
def lambda_handler(message, context):
```

This decorator validates, serializes and flushes any metrics data logged in the app to stdout. When creating metrics we need to define a namespace. We can add this as a parameter to the decorator or via envrionment variable as shown in the step below.

Lastly, let's add the decorator for tracing.

```python
@logger.inject_lambda_context
@metrics.log_metrics
@tracer.capture_lambda_handler
def lambda_handler(message, context):
```

This decorator automatically captures any response or exception raised by the Lambda handler and writes it into the tracing metadata. It also setups the ColdStart annotation so filtering is made easier when troubleshooting.

We also need to grant Lambda permission to log traces to AWS X-Ray. We do this in SAM by setting Tracing to Active in each of our functions. We can use the Globals section to apply to each function.

```yaml
Globals:
  Function:
    Timeout: 30
    Tracing: Active
```

While we are here, lets enable API tracing as well so we can capture end-to-end visibilty of our service.

```yaml
Globals:
  Api:    
    TracingEnabled: true
  Function:
    Timeout: 30
    Tracing: Active
```

We can also capture traces in other methods of our Lambda function using the following method decorator

```python
@tracer.capture_method
def helper_Method(params):
```

We can turn tracing on or off using the POWERTOOLS_TRACE_DISABLED environment variable. Useful when running unit tests locally or as part of automated testing stages of CI pipeline.

To complete the setup we need to add a couple of envrionment variables to each of our Lambda functions. To do this consistency, we'll add these to the Globals section of our SAM template.

```yaml
Globals:
  Api:    
    TracingEnabled: true
  Function:
    Timeout: 30
    Tracing: Active
    Environment:
      Variables:
        LOG_LEVEL: INFO
        POWERTOOLS_SERVICE_NAME: well-architected-serverless
        POWERTOOLS_LOGGER_LOG_EVENT: True
        POWERTOOLS_METRICS_NAMESPACE: well-architected-serverless    
```

| Variable | Description | Sample value|
|---|---|---|
| LOG_LEVEL | Sets how verbose Logger should be (INFO, by default)| INFO |
| POWERTOOLS_SERVICE_NAME | Sets service key that will be present across all log statements | well-architected-serverless |
| POWERTOOLS_LOGGER_LOG_EVENT | Log the incoming event | True |
| POWERTOOLS_METRICS_NAMESPACE | Logical container where all metrics will be placed | well-architected-serverless |
| POWERTOOLS_TRACE_DISABLED | Disable trace events globally | 0 |

With our setup complete, lets enhance our code to write out logs and metrics in a standardised well-architectured way

## Logging

Start by converting those print statements into logger calls using the built in log level convience methods. 

For example:

A simple log statement

```python
# Simple log statement
logger.info('## List Entities')
```

The structure of the log entry will look something like this

```json
{
    "level": "INFO",
    "location": "lambda_handler:18",
    "message": "## List Entities",
    "timestamp": "2021-03-14 09:14:00,181",
    "service": "well-architected-serverless",
    "sampling_rate": 0,
    "cold_start": true,
    "function_name": "well-architected-serverless-ListEntitiesFunction-1EGOGZHDCJ8W9",
    "function_memory_size": "128",
    "function_arn": "arn:aws:lambda:us-east-1:752419465350:function:well-architected-serverless-ListEntitiesFunction-1EGOGZHDCJ8W9",
    "function_request_id": "d4809e0b-26f7-4389-b14c-055f28340868",
    "xray_trace_id": "1-604dd3d7-64dd892e0334dfe63a8693b7"
}
```

Log with complex object

```python
# Log using object structure
logger.info({
    "environment": environment,
    "region": region
})
```

The structure of the log entry will look something like this

```json
{
    "level": "INFO",
    "location": "lambda_handler:37",
    "message": {
        "environment": "false",
        "region": "us-east-1"
    },
    "timestamp": "2021-03-14 09:14:00,182",
    "service": "well-architected-serverless",
    "sampling_rate": 0,
    "cold_start": true,
    "function_name": "well-architected-serverless-ListEntitiesFunction-1EGOGZHDCJ8W9",
    "function_memory_size": "128",
    "function_arn": "arn:aws:lambda:us-east-1:752419465350:function:well-architected-serverless-ListEntitiesFunction-1EGOGZHDCJ8W9",
    "function_request_id": "d4809e0b-26f7-4389-b14c-055f28340868",
    "xray_trace_id": "1-604dd3d7-64dd892e0334dfe63a8693b7"
}
```

Log exceptions

```python
except Exception:
    logger.exception('Caught exception')
    raise
```

The structure of the log entry will look something like this

```json
{
    "level": "ERROR",
    "location": "lambda_handler:70",
    "message": "Caught exception",
    "timestamp": "2021-03-14 09:14:02,203",
    "service": "well-architected-serverless",
    "sampling_rate": 0,
    "cold_start": true,
    "function_name": "well-architected-serverless-ListEntitiesFunction-1EGOGZHDCJ8W9",
    "function_memory_size": "128",
    "function_arn": "arn:aws:lambda:us-east-1:752419465350:function:well-architected-serverless-ListEntitiesFunction-1EGOGZHDCJ8W9",
    "function_request_id": "d4809e0b-26f7-4389-b14c-055f28340868",
    "exception": "Traceback (most recent call last):\n  File \"/var/task/app.py\", line 56, in lambda_handler\n    results = table.scan()\n  File \"/var/task/boto3/resources/factory.py\", line 520, in do_action\n    response = action(self, *args, **kwargs)\n  File \"/var/task/boto3/resources/action.py\", line 83, in __call__\n    response = getattr(parent.meta.client, operation_name)(*args, **params)\n  File \"/var/task/botocore/client.py\", line 357, in _api_call\n    return self._make_api_call(operation_name, kwargs)\n  File \"/var/task/aws_xray_sdk/ext/botocore/patch.py\", line 38, in _xray_traced_botocore\n    return xray_recorder.record_subsegment(\n  File \"/var/task/aws_xray_sdk/core/recorder.py\", line 435, in record_subsegment\n    return_value = wrapped(*args, **kwargs)\n  File \"/var/task/botocore/client.py\", line 676, in _make_api_call\n    raise error_class(parsed_response, operation_name)\nbotocore.errorfactory.ResourceNotFoundException: An error occurred (ResourceNotFoundException) when calling the Scan operation: Requested resource not found",
    "xray_trace_id": "1-604dd3d7-64dd892e0334dfe63a8693b7"
}
```

## Metrics

To demonstrate metrics, let's add metrics to our create_entity and delete_entity functions. Metrics are added using the add_metric method. Custom metric dimensions can be added using the add_dimension method for metric aggregation.

For example:

```python
# Create metric for successful entity being added
metrics.add_dimension(name="Region", value=region)
metrics.add_metric(name="EntityCreated", unit=MetricUnit.Count, value=1)

return {
    'statusCode': 201,
    'headers': {},
    'body': json.dumps({'Message': 'Entity created'})
}
```

The structure of the log entry will look something like this

```json
{
    "_aws": {
        "Timestamp": 1615711712586,
        "CloudWatchMetrics": [
            {
                "Namespace": "well-architected-serverless",
                "Dimensions": [
                    [
                        "Region",
                        "service"
                    ]
                ],
                "Metrics": [
                    {
                        "Name": "EntityCreated",
                        "Unit": "Count"
                    }
                ]
            }
        ]
    },
    "Region": "us-east-1",
    "service": "well-architected-serverless",
    "EntityCreated": [
        1
    ]
}
```

## Tracing

In addition to the automatic capture of exceptions and responses, we can manually add trace metadata and annotations.

To manually add trace metadata

```python
# Trace DynamoDB results as custom metadata
tracer.put_metadata(key="dynamodb_results", value=results)
```

As mentioned above, exceptions and responses are captured in trace output by default. Should we wish to disable these we can provide additional params to the handler decorator

```python
@tracer.capture_lambda_handler(capture_error=False)
```

```python
@tracer.capture_lambda_handler(capture_response=False)
```

We can also disable tracing altogther (e.g. in production environments) using the POWERTOOLS_TRACE_DISABLED environment variable

## Build and deploy the sample application

To build and deploy your application for the first time, run the following:

```bash
sam build --use-container
sam deploy --guided
```

Use the following responses during the guided deployment

```bash
Stack Name [basic-lambda-service]: well-architected-serverless
AWS Region [us-east-1]: 
Parameter REGION [us-east-1]: 
#Shows you resources changes to be deployed and require a 'Y' to initiate deploy
Confirm changes before deploy [y/N]: y
#SAM needs permission to be able to create roles to connect to the resources in your template
Allow SAM CLI IAM role creation [Y/n]: Y
ListEntitiesFunction may not have authorization defined, Is this okay? [y/N]: y
GetEntityFunction may not have authorization defined, Is this okay? [y/N]: y
CreateEntityFunction may not have authorization defined, Is this okay? [y/N]: y
DeleteEntityFunction may not have authorization defined, Is this okay? [y/N]: y
Save arguments to configuration file [Y/n]: Y
SAM configuration file [samconfig.toml]: 
SAM configuration environment [default]: 
```

You can find your API Gateway Endpoint URL in the output values displayed after deployment. Use curl, web browser or API Gateway console to generate some API requests and explore CloudWatch Logs, Metrics, and X-Ray consoles to observe your deployed serverless application.

## Conclusion

In this post we covered installing and setting up the AWS Lambda PowerTools for Python to provide an easy to use framework that implement observability best practices. We applied the framework to the basic lambda service sample serverless application and deployed it to AWS.



# Explore the Basic Lambda Service further

This project contains source code and supporting files for a basic Lambda service that you can deploy with the SAM CLI. The basic lambda service application exposes RESTful API endpoints to invoke serverless CRUD operations backed by a NoSQL serverless data store.

The profject includes the following files and folders.

- template.yaml - A template that defines the application's AWS resources.
- src - Code for the application's Lambda function.
- dynamodb - Docker compose file for running DynamoDBLocal in a shared docker network and a persisted volume.
- events - Invocation events that you can use to invoke the function.
- tests - Unit tests for the application code. 

The application uses several AWS resources, including Lambda functions, API Gateway, and DynamoDB. These resources are defined in the `template.yaml` file in this project. You can update the template to add AWS resources through the same deployment process that updates your application code.

## Deploy the sample application

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

To use the SAM CLI, you need the following tools.

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build and deploy your application for the first time, run the following in your shell:

```bash
sam build --use-container
sam deploy --guided
```

The first command will build the source of your application. The second command will package and deploy your application to AWS, with a series of prompts:

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
* **AWS Region**: The AWS region you want to deploy your app to.
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modified IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

You can find your API Gateway Endpoint URL in the output values displayed after deployment.

## Use the SAM CLI to build and test locally

Build your application with the `sam build --use-container` command.

The SAM CLI installs dependencies defined in each function's `requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

```bash
sam build --use-container
```

## DynamoDB

It is recommended to host DynamoDB locally using Docker and use NoSQL Workbench's Operation builder to visualise the data.

Spin up a DynamoDB local instance using docker-compose specifying a persisted volume and internal network. 

```bash
docker-compose -f ./data/docker-compose.yaml up
```

Create the table first time through so we can test locally
```bash
aws dynamodb create-table --table-name Entities --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 --endpoint-url http://localhost:8000
```

Verify its available

```bash
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

## Lambda

Test a single function by invoking it directly with a test event. An event is a JSON document that represents the input that the function receives from the event source. Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `sam local invoke` command.

Start with adding some data into our local DynamoDB table

```bash
sam local invoke CreateEntityFunction --event events/create_entities_event.json --docker-network serverless-local
```

Now test we can list all entities in DynamoDB

```bash
sam local invoke ListEntitiesFunction --event events/list_entities_event.json --docker-network serverless-local
```

## API Gateway

The SAM CLI can also emulate your application's API. Use the `sam local start-api` to run the API locally on port 3000.

>Note: Here we also use the shared docker network we created eariler so API Gateway can forward requests to our Lambda functions running as containers.

```bash
sam local start-api --docker-network serverless-local
```

Test API calls using curl, Postman, or GET operations via the browser

```bash
curl http://localhost:3000/entities
curl http://localhost:3000/entities/1
```

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated by your deployed Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
sam logs -n ListEntitiesFunction --stack-name basic-lambda-service --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
aws cloudformation delete-stack --stack-name basic-lambda-service
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)
