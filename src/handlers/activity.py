import json
from app import app
from managers.activity_manager import ActivityManager
from aws_lambda_powertools import Logger

logger = Logger()


@app.post("/activities")
def get_activities():
    """
    Retrieve all activities from the Activity table.

    Returns:
        dict: JSON response containing the list of activities or an error message.
    """
    try:
        user_info = app.current_event.json_body
        results = ActivityManager.get_all_activities(user_info)
        return {"statusCode": 200, "body": json.dumps(results, default=str)}
    except Exception as e:
        logger.error(f"Failed to list activities: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }


@app.put("/activities")
def save_activity():
    """
    Save a new activity to the Activity table.

    Returns:
        dict: JSON response indicating success or failure of the operation.
    """
    try:
        data = app.current_event.json_body

        # Validate required fields
        if not all(
            [
                data.get("firstName"),
                data.get("lastName"),
                data.get("bucketName"),
                data.get("action"),
                data.get("userName"),
            ]
        ):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields"}),
            }

        ActivityManager.save_activity(data)

        return {
            "statusCode": 201,
            "body": json.dumps({"message": "Activity saved successfully"}),
        }
    except Exception as e:
        logger.error(f"Failed to save activity: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
