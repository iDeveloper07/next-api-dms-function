import json
from app import app
from botocore.exceptions import BotoCoreError, ClientError
from aws_lambda_powertools import Logger
from managers.policy_manager import PolicyManager

logger = Logger()


@app.post("/policies")
def policies_list():
    try:
        user_info = app.current_event.json_body
        user_name = user_info.get("user_name")
        policies = PolicyManager.list_policies(user_name)
        return policies
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi policies: {e}")
        return {"error": "Failed to list policies from Wasabi"}, 500


@app.post("/policy/create")
def create_policy():
    try:
        policy_data = app.current_event.json_body

        bucket_permissions = policy_data.get("bucket_permissions")
        policy_name = policy_data.get("policy_name")
        user_name = policy_data.get("user_name")

        if not bucket_permissions or not policy_name:
            return {"error": "Missing User Info"}, 400

        res = PolicyManager.create_s3_policy(bucket_permissions, policy_name, user_name)
        return res

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to create Wasabi Role: {e}")
        return {"error": "Failed to create role from Wasabi"}, 500


@app.post("/policy/permission")
def get_user_permission():
    try:
        policy_data = app.current_event.json_body
        policyArn = policy_data.get("policyArn")
        user_name = policy_data.get("user_name")

        permissions = PolicyManager.generate_policy_input_from_existing(policyArn, user_name)
        return permissions
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to list Wasabi Users: {e}")
        return {"error": "Failed to list User Info from Wasabi"}, 500


@app.post("/policy/update")
def update_policy():
    try:
        policy_data = app.current_event.json_body

        bucket_permissions = policy_data.get("bucket_permissions")
        policy_arn = policy_data.get("policy_arn")
        user_name = policy_data.get("user_name")

        if not bucket_permissions or not policy_arn:
            return {"error": "Missing User Info"}, 400

        res = PolicyManager.update_s3_policy(bucket_permissions, policy_arn, user_name)
        return res

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to create Wasabi Role: {e}")
        return {"error": "Failed to create role from Wasabi"}, 500

@app.post("/allowed_buckets")
def get_allowed_buckets():
    """
    Retrieve all activities from the Activity table.

    Returns:
        dict: JSON response containing the list of activities or an error message.
    """
    try:
        user_info = app.current_event.json_body
        user_name = user_info.get("user_name")
        
        results = PolicyManager.get_available_buckets(user_name)
        return {"statusCode": 200, "body": json.dumps(results, default=str)}
    except Exception as e:
        logger.error(f"Failed to list activities: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }