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
from module.users import (
    list_users,
    get_user_details,
    get_assigned_policies,
    attach_policy_to_user,
    remove_policy_from_user,
    update_user_info,
    create_wasabi_subaccount,
    create_wasabi_subuser,
)
from module.bucket import (
    delete_bucket,
    delete_folder,
    delete_object,
    get_storage_utilizations,
)
from module.policy import (
    list_policies,
    create_s3_policy,
    generate_policy_input_from_existing,
    update_s3_policy,
)

logger = Logger()
app = APIGatewayRestResolver()

# Read environment variables
server_url = os.getenv("SERVER_URL")
wasabi_access_key = os.getenv("WASABI_ACCESS_KEY")
wasabi_secret_key = os.getenv("WASABI_SECRET_KEY")
wasabi_endpoint_url = os.getenv("WASABI_ENDPOINT_URL", "https://s3.wasabisys.com")


# To test RDS Proxy connection
@app.get("/test/rds_proxy")
def test_rds_proxy():
    update_query = """
    -- Truncate the bucket_audit table (removes all rows)
    TRUNCATE TABLE bucket_audit;

    -- Add a new column called 'username' with data type VARCHAR(255)
    ALTER TABLE bucket_audit
        ADD COLUMN username VARCHAR(255);
    """
    truncate_query = """
    -- Truncate the bucket_audit table (removes all rows)
    TRUNCATE TABLE bucket_audit;
    """

    # execute_query(update_query)
    create_tanants_table = """
        DROP TABLE IF EXISTS tenants;  
        CREATE TABLE tenants (
            id SERIAL PRIMARY KEY,
            tenant_id VARCHAR(255) NOT NULL,             
            wasabi_sub_account_id VARCHAR(255) NOT NULL,
            wasabi_sub_account_num VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            access_key VARCHAR(255) NOT NULL,
            secret_key VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """

    drop_tenants_table = """
             
    """
    select_query = "SELECT * FROM tenants;"
    # results = execute_query(drop_tenants_table)
    results = execute_query(create_tanants_table)

    return json.dumps(results, default=str)


@app.get("/wasabi/buckets")
def list_wasabi_buckets():
    # Set up the boto3 client for Wasabi with the correct region
    s3_client = boto3.client(
        "s3",
        endpoint_url=wasabi_endpoint_url,
        aws_access_key_id=wasabi_access_key,
        aws_secret_access_key=wasabi_secret_key,
        region_name="us-east-1",  # Explicitly specify the correct region
    )

    try:
        response = s3_client.list_buckets()
        buckets = response.get("Buckets", [])
        return json.dumps(buckets, cls=DateTimeEncoder)
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi buckets: {e}")
        return json.dumps(
            {"error": "Failed to list buckets from Wasabi"}, cls=DateTimeEncoder
        ), 500


# Role management
@app.get("/roles")
def roles_get_list():
    try:
        roles = get_role_list()
        return roles
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi Roles: {e}")
        return json.dumps(
            {"error": "Failed to list roles from Wasabi"}, cls=DateTimeEncoder
        ), 500


@app.post("/roles")
def roles_create():
    try:
        # Fetch and parse the JSON body of the request
        role_data = app.current_event.json_body

        # Access dictionary keys properly
        role_name = role_data.get("RoleName")
        assume_role_policy_document = role_data.get("AssumeRolePolicyDocument")

        if not role_name or not assume_role_policy_document:
            return {"error": "Missing RoleName or AssumeRolePolicyDocument"}, 400

        # Call the create IAM role function
        res = create_iam_role(role_name, assume_role_policy_document)
        return res

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to create Wasabi Role: {e}")
        return {"error": "Failed to create role from Wasabi"}, 500


# User Management
@app.put("/subAccount")
def create_sub_account():
    subAccount_info = app.current_event.json_body
    tenant_id = subAccount_info.get("tenant_id")
    seed_user_id = subAccount_info.get("seed_user_id")
    return create_wasabi_subaccount(tenant_id, seed_user_id)
    
@app.get("/users")
def users_list():
    try:
        users = list_users()
        return users
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi Users: {e}")
        return json.dumps(
            {"error": "Failed to list users from Wasabi"}, cls=DateTimeEncoder
        ), 500

@app.put("/users")
def create_user():
    try:
        user_info = app.current_event.json_body
        user_name = user_info.get("UserName")
        res = create_wasabi_subuser(user_name)
        return res
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to create new Wasabi sub User: {e}")
        return json.dumps(
            {"error": "Failed to create new Wasabi sub User"}, cls=DateTimeEncoder
        ), 500
    

@app.get("/users/<userName>")
def get_user_info(userName: str):
    try:
        userInfo = get_user_details(userName)
        return userInfo
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi Users: {e}")
        return json.dumps(
            {"error": "Failed to list User Info from Wasabi"}, cls=DateTimeEncoder
        ), 500


@app.get("/users/<userName>/policies")
def get_user_policies(userName: str):
    try:
        assigned_policies = get_assigned_policies(userName)
        return assigned_policies
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi Users: {e}")
        return json.dumps(
            {"error": "Failed to list User Info from Wasabi"}, cls=DateTimeEncoder
        ), 500


@app.post("/users/assgin/policy")
def assgin_policy():
    try:
        # Fetch and parse the JSON body of the request
        role_data = app.current_event.json_body

        # Access dictionary keys properly
        user_name = role_data.get("UserName")
        policy_arn = role_data.get("PolicyArn")

        if not user_name or not policy_arn:
            return {"error": "Missing UserName or PolicyArn"}, 400

        # Call the create IAM role function
        res = attach_policy_to_user(user_name, policy_arn)
        return res

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to create Wasabi Role: {e}")
        return {"error": "Failed to create role from Wasabi"}, 500


@app.delete("/users/policy")
def remove_policy():
    try:
        # Fetch and parse the JSON body of the request
        role_data = app.current_event.json_body

        # Access dictionary keys properly
        user_name = role_data.get("UserName")
        policy_arn = role_data.get("PolicyArn")

        if not user_name or not policy_arn:
            return {"error": "Missing UserName or PolicyArn"}, 400

        # Call the create IAM role function
        res = remove_policy_from_user(user_name, policy_arn)
        return res

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to create Wasabi Role: {e}")
        return {"error": "Failed to create role from Wasabi"}, 500


@app.put("/users/update")
def update_user():
    try:
        # Fetch and parse the JSON body of the request
        user_data = app.current_event.json_body

        # Access dictionary keys properly
        user_name = user_data.get("UserName")
        new_user_name = user_data.get("NewUserName")
        new_path = user_data.get("NewPath")
        active_status = user_data.get("Activate")

        if not user_name or not new_user_name or not new_path:
            return {"error": "Missing User Info"}, 400

        # Call the create IAM role function
        res = update_user_info(user_name, new_user_name, new_path, active_status)
        return res

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to create Wasabi Role: {e}")
        return {"error": "Failed to create role from Wasabi"}, 500


@app.post("/bucket/delete")
def bucket_delete():
    data = app.current_event.json_body

    bucket_name = data.get("bucket_name")
    key = data.get("key", "")  # The object or folder to delete
    action = data.get("action")  # 'bucket', 'folder', or 'object'

    if not bucket_name or not action:
        return {"error": "Missing required parameters: bucket_name and action"}, 400

    if action == "bucket":
        return delete_bucket(bucket_name)
    elif action == "folder":
        return delete_folder(bucket_name, key)
    elif action == "object":
        return delete_object(bucket_name, key)
    else:
        return {
            "error": f"Invalid action: {action}. Expected 'bucket', 'folder', or 'object'."
        }, 500


@app.get("/activities")
def get_activities():
    try:
        select_query = "SELECT * FROM bucket_audit;"
        results = execute_query(select_query)
        return json.dumps(results, default=str)
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list user activities: {e}")
        return json.dumps(
            {"error": "Failed to list user activities"}, cls=DateTimeEncoder
        ), 500


@app.get("/policies")
def policies_list():
    try:
        policies = list_policies()
        return policies
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi policies: {e}")
        return json.dumps(
            {"error": "Failed to list policies from Wasabi"}, cls=DateTimeEncoder
        ), 500


@app.post("/policy/create")
def create_policy():
    try:
        # Fetch and parse the JSON body of the request
        policy_data = app.current_event.json_body

        # Access dictionary keys properly
        bucket_permissions = policy_data.get("bucket_permissions")
        policy_name = policy_data.get("policy_name")

        if not bucket_permissions or not policy_name:
            return {"error": "Missing User Info"}, 400

        # Call the create IAM role function
        res = create_s3_policy(bucket_permissions, policy_name)
        return res

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to create Wasabi Role: {e}")
        return {"error": "Failed to create role from Wasabi"}, 500


@app.post("/policy/permission")
def get_user_permission():
    try:
        policy_data = app.current_event.json_body
        policyArn = policy_data.get("policyArn")
        permissions = generate_policy_input_from_existing(policyArn)
        return permissions
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi Users: {e}")
        return json.dumps(
            {"error": "Failed to list User Info from Wasabi"}, cls=DateTimeEncoder
        ), 500


@app.post("/policy/update")
def update_policy():
    try:
        # Fetch and parse the JSON body of the request
        policy_data = app.current_event.json_body

        # Access dictionary keys properly
        bucket_permissions = policy_data.get("bucket_permissions")
        policy_arn = policy_data.get("policy_arn")

        if not bucket_permissions or not policy_arn:
            return {"error": "Missing User Info"}, 400

        # Call the create IAM role function
        res = update_s3_policy(bucket_permissions, policy_arn)
        return res

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to create Wasabi Role: {e}")
        return {"error": "Failed to create role from Wasabi"}, 500


@app.get("/utilizations")
def get_utilizations():
    try:
        # Call the create IAM role function
        res = get_storage_utilizations()
        return res

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to get the storage info : {e}")
        return {"error": "Failed to get the storage info "}, 500


@middleware_after
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    response = app.resolve(event, context)

    # Serialize the response body using DateTimeEncoder
    if "body" in response and isinstance(response["body"], dict):
        response["body"] = json.dumps(response["body"], cls=DateTimeEncoder)

    return response
