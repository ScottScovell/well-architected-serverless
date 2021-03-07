# Basic Lambda Service

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
