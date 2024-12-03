import json
from app import app
from aws_lambda_powertools import Logger
from helpers.utils import DateTimeEncoder
from managers.user_manager import UserManager

logger = Logger()

@app.get("/users")
def list_users():
    """
    Retrieves a list of all users from the RDS database.
    
    Returns:
        dict: The list of users if successful, or an error message in case of failure.
    """
    try:
        logger.info("Received request to list all users.")

        # Call the manager to retrieve all users
        users = UserManager.get_all_users()

        if not users:
            logger.info("No users found.")
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'No users found.'})
            }

        logger.info(f"Retrieved {len(users)} users from RDS.")
        return {
            'statusCode': 200,
            'body': json.dumps(users, cls=DateTimeEncoder) 
        }

    except Exception as e:
        logger.error(f"Error occurred while listing users: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


@app.post("/user")
def get_user():
    """
    Retrieves user information from RDS. If the user doesn't exist, creates the user in Wasabi 
    and stores the user under the specific tenant in RDS.
    
    Returns:
        dict: The user information, including status and data if successful, or an error message in case of failure.
    """
    try:
        data = app.current_event.json_body
        user_name = data.get("user_name")
        is_admin = data.get("is_admin", False)

        if not user_name:
            logger.error("Missing 'user_name' in request.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'user_name is required'})
            }

        logger.info(f"Received request to retrieve user: {user_name}")

        user_info = UserManager.get_or_create_user(user_name, is_admin)

        if not user_info:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to retrieve or create user'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(user_info, cls=DateTimeEncoder)
        }

    except Exception as e:
        logger.error(f"Error occurred while retrieving or creating user: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
