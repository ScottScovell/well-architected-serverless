
# Part 1 - Enabling CloudWatch Lambda Insights

CloudWatch Lambda Insights is a monitoring and troubleshooting solution for serverless applications running on AWS Lambda. The solution collects, aggregates, and summarizes system-level metrics including CPU time, memory, disk, and network. It also collects, aggregates, and summarizes diagnostic information such as cold starts and Lambda worker shutdowns to help you isolate issues with your Lambda functions and resolve them quickly.

Lambda Insights uses a new CloudWatch Lambda extension, which is provided as a Lambda layer. When you install this extension on a Lambda function, it collects system-level metrics and emits a single performance log event for every invocation of that Lambda function. CloudWatch uses embedded metric formatting to extract metrics from the log events.

See [AWS Docs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Lambda-Insights.html) for more information

## Add the Lambda Insights Layer

To add the layer to all functions, use the Globals section and specify which version of the Lambda extension to use.

>Note: Available versions of the Lambda Insights Extension can be found [here](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Lambda-Insights-extension-versions.html)

Add the Layer to the Globals section of our `template.yaml` file as follows

```yaml
Globals:
  Function:
    Timeout: 30
    Layers:
      - !Sub "arn:aws:lambda:${AWS::Region}:580247275435:layer:LambdaInsightsExtension:14"
```

Now add the `CloudWatchLambdaInsightsExecutionRolePolicy` IAM policy to each function (currently not supported in the Globals section)

```yaml
  ListEntitiesFunction:
    Type: AWS::Serverless::Function
    Properties:
      ...
      Policies:
        - CloudWatchLambdaInsightsExecutionRolePolicy
        - DynamoDBCrudPolicy:
            TableName: !Ref EntitiesTable
```

Use the SAM CLI to validate the changes to the SAM template

```bash
sam validate
```

You should see `template.yaml is a valid SAM Template`

Now use the SAM CLI to build and deploy the application to AWS.

```bash
sam build --use-container
sam deploy --guided
```

Use the following settings during the guided deployment

```bash
Setting default arguments for 'sam deploy'
=========================================
Stack Name [sam-app]: well-architected-serverless
AWS Region [us-east-1]: 
Parameter REGION [us-east-1]: 
Confirm changes before deploy [y/N]: y
Allow SAM CLI IAM role creation [Y/n]: Y
ListEntitiesFunction may not have authorization defined, Is this okay? [y/N]: y
GetEntityFunction may not have authorization defined, Is this okay? [y/N]: y
CreateEntityFunction may not have authorization defined, Is this okay? [y/N]: y
DeleteEntityFunction may not have authorization defined, Is this okay? [y/N]: y
Save arguments to configuration file [Y/n]: Y
SAM configuration file [samconfig.toml]: 
SAM configuration environment [default]: 
```

## Viewing Lambda Insights in the CloudWatch Console

Generate some traffic using the API Gatway console, Postman, or curl to execute requests against our application

For example, the following bash command simulates 100 invocations of the ListEntitiesFunction via the deployed API Gateway endpoint.

```bash
for run in {1..100}; do curl https://3zk9g9go06.execute-api.us-east-1.amazonaws.com/Prod/entities/; sleep 5; done
```

In the CloudWatch Console, navigate to Lambda Insights and select Multi-Function to view aggregated metrics for our Lambda functions. Switch to Single-function and select a specific Lamnda function to view performance metrics, performance logs, and application logs for that function.

# Exploring the Basic Lambda Service

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
