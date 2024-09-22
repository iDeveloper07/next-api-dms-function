import requests
import os
from requests import Response
import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

from middleware import middleware_after
from rds_proxy import execute_query
from utils import DateTimeEncoder  # Import the custom DateTimeEncoder

from module.role import get_role_list, create_iam_role

logger = Logger()
app = APIGatewayRestResolver()

# Read environment variables
server_url = os.getenv("SERVER_URL")
wasabi_access_key = os.getenv("WASABI_ACCESS_KEY")
wasabi_secret_key = os.getenv("WASABI_SECRET_KEY")
wasabi_endpoint_url = os.getenv("WASABI_ENDPOINT_URL", "https://s3.wasabisys.com")


@app.get("/todos")
def get_todos():
    todos: Response = requests.get(f"{server_url}/todos")
    todos.raise_for_status()

    # Serialize result using DateTimeEncoder
    return json.dumps(todos.json()[:10], cls=DateTimeEncoder)


@app.get("/todos/<todo_id>")
def get_todo_by_id(todo_id: str):
    todo: Response = requests.get(f"{server_url}/todos/{todo_id}")
    todo.raise_for_status()

    # Serialize result using DateTimeEncoder
    return json.dumps(todo.json(), cls=DateTimeEncoder)


@app.post("/todos")
def create_todo():
    todo_data: dict = app.current_event.json_body  # Deserialize JSON string to dict
    todo: Response = requests.post(f"{server_url}/todos", json=todo_data)
    todo.raise_for_status()

    # Serialize result using DateTimeEncoder
    return json.dumps(todo.json(), cls=DateTimeEncoder)


@app.put("/todos/<todo_id>")
def update_todo(todo_id: str):
    todo_data: dict = app.current_event.json_body  # Deserialize JSON string to dict
    todo: Response = requests.put(f"{server_url}/todos/{todo_id}", json=todo_data)
    todo.raise_for_status()

    # Serialize result using DateTimeEncoder
    return json.dumps(todo.json(), cls=DateTimeEncoder)


@app.delete("/todos/<todo_id>")
def delete_todo(todo_id: str):
    todo: Response = requests.delete(f"{server_url}/todos/{todo_id}")
    todo.raise_for_status()

    return json.dumps({"todo": todo_id}, cls=DateTimeEncoder)


# To test RDS Proxy connection
@app.get("/test/rds_proxy")
def test_rds_proxy():
    result = execute_query("""SELECT * FROM todos LIMIT 10""")

    # Serialize result using DateTimeEncoder
    return json.dumps(result[0] if result else {}, cls=DateTimeEncoder)

@app.get("/wasabi/buckets")
def list_wasabi_buckets():
    # Set up the boto3 client for Wasabi with the correct region
    s3_client = boto3.client(
        "s3",
        endpoint_url=wasabi_endpoint_url,
        aws_access_key_id=wasabi_access_key,
        aws_secret_access_key=wasabi_secret_key,
        region_name="us-east-1"  # Explicitly specify the correct region
    )

    try:
        response = s3_client.list_buckets()
        buckets = response.get("Buckets", [])
        return json.dumps({"buckets": buckets}, cls=DateTimeEncoder)
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi buckets: {str(e)}")
        return json.dumps({"error": "Failed to list buckets from Wasabi"}, cls=DateTimeEncoder), 500

# Role management
@app.get("/roles")
def roles_get_list():
    try:
        roles = get_role_list()
        return roles
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi Roles: {str(e)}")
        return json.dumps({"error": "Failed to list roles from Wasabi"}, cls=DateTimeEncoder), 500
        
@app.post("/roles/create")
def roles_create():
    try:
        # Fetch and parse the JSON body of the request
        role_data = app.current_event.json_body
        
        # Access dictionary keys properly
        role_name = role_data.get('RoleName')
        assume_role_policy_document = role_data.get('AssumeRolePolicyDocument')

        if not role_name or not assume_role_policy_document:
            return {"error": "Missing RoleName or AssumeRolePolicyDocument"}, 400

        # Call the create IAM role function
        res = create_iam_role(role_name, assume_role_policy_document)
        return {"res": res}
    
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to create Wasabi Role: {str(e)}")
        return {"error": "Failed to create role from Wasabi"}, 500

@middleware_after
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    response = app.resolve(event, context)

    # Serialize the response body using DateTimeEncoder
    if "body" in response and isinstance(response["body"], dict):
        response["body"] = json.dumps(response["body"], cls=DateTimeEncoder)

    return response
