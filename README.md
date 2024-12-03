# next-sam-dms-api

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI. It includes the following files and folders.

- **`src`** - Code for the application's Lambda function for CRUD REST API.
- **`events`** - Invocation events that you can use to invoke the function.
- **`tests`** - Unit tests for the application code. 
- **`template.yaml`** - A template that defines the application's AWS resources.

The application uses several AWS resources, including Lambda functions and an API Gateway API. These resources are defined in the template.yaml file in this project. 



## Requirements

**Make sure you have the following installed before you proceed**

* AWS CLI - [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) configured with Administrator permission
* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3](https://www.python.org/downloads/) and [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html) installed
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)
* [PyCharm](https://www.jetbrains.com/pycharm/download) / [VSCode](https://code.visualstudio.com/download)


## Working with this project

### Quick start

```bash
# Change directory
cd next-sam-dms-api

# Setup your virtualenv and install packages
virtualenv venv
source venv/bin/activate
pip install -r ./src/requirements.txt
pip install -r ./tests/requirements.txt

# Unit test
python -m pytest -v

# Build SAM
sam build --use-container

# Test lambda function by invoking event locally
sam local invoke ApiFunction --event events/get_todos.json

# Deploy
sam deploy --guided
```


### Use the SAM CLI to build and test locally

Build your application with the `sam build --use-container` command.

```bash
sam build --use-container
```

The SAM CLI installs dependencies defined in `src/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is a JSON document that represents the input that the function receives from the event source. Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `sam local invoke` command.

```bash
sam local invoke ApiFunction --event events/get_todos.json
```

The SAM CLI can also emulate your application's API. Use the `sam local start-api` to run the API locally on port 3000.

```bash
sam local start-api
curl http://localhost:3000/todos
```

The SAM CLI reads the application template to determine the API's routes and the functions that they invoke. The `Events` property on each function's definition includes the route and method for each path.

```yaml
Events:
  GetAllTodos:
    Type: Api
    Properties:
      Path: /todos
      Method: get
```

### Use PyCharm IDE to debug and test locally
Using AWS Toolkits

[AWS Toolkits](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-debugging.html) are integrated development environment (IDE) plugins that provide you with the ability to perform many common debugging tasks, like setting breakpoints, inspecting variables, and executing function code one line at a time. AWS Toolkits make it easier for you to develop, debug, and deploy serverless applications that are built using AWS SAM. They provide an experience for building, testing, debugging, deploying, and invoking Lambda functions that's integrated into your IDE.

To install AWS Toolkit plugin in PyCharm, navigate to File > Settings > Plugins > Marketplace and search for `AWS Toolkit` and install it.




Build Lambda Layers

We will build psycopg2 lambda layer for postgres.

```bash
# Change directory
cd next-sam-dms-api

# Build psycopg2 layer
./build-layers.sh
```

Setting up [Postgres](https://hub.docker.com/_/postgres)

If you are using Rds Proxy in your AWS SAM template, you need to setup Postgres locally to test and debug.

```bash
# Change directory
cd next-sam-dms-api

# Start Postgres container
docker-compose up
```


Now you can run your project in debug mode in PyCharm.


### Add a resource to your application

The application template uses AWS Serverless Application Model (AWS SAM) to define application resources. AWS SAM is an extension of AWS CloudFormation with a simpler syntax for configuring common serverless application resources such as functions, triggers, and APIs. For resources not included in [the SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md), you can use standard [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html) resource types.

### Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated by your deployed Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
sam logs -n ApiFunction --stack-name next-sam-dms-api --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

### Tests

Tests are defined in the `tests` folder in this project. Use PIP to install the test dependencies and run tests.

```bash
pip install -r tests/requirements.txt
# unit test
python -m pytest -v
# integration test, requiring deploying the stack first.
# Create the env variable AWS_SAM_STACK_NAME with the name of the stack we are testing
AWS_SAM_STACK_NAME="next-sam-dms-api" python -m pytest tests/integration -v
```

### Deploy
To deploy the application, run the following command:

```bash
$ sam deploy --guided
```

The `sam deploy` command will package and deploy your application to AWS, with a series of prompts:

- **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
- **AWS Region**: The AWS region you want to deploy your app to.
- **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
- **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modifies IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
- **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

You can find your API Gateway Endpoint URL in the output values displayed after deployment.



### Deploy with CI/CD systems and pipelines

Please read this [guide](./deploy-guide.md) to deploy with CI/CD systems.


### Cleanup

To delete your application that you created, use the AWS CLI.

```bash
sam delete --stack-name "next-sam-dms-api"
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)
