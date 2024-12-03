from aws_lambda_powertools import Logger
from models.activity_model import Activity
from managers.policy_manager import PolicyManager
from services.logging_service import log_execution_time

logger = Logger()


class ActivityManager:

    @staticmethod
    @log_execution_time
    def get_all_activities(user_info):
        """
        Retrieve all activities using the Activity model.

        Returns:
            list: List of Activity objects.
        """
        try:
            logger.info("Fetching all activities.")
            user_name = user_info.get("user_name")
            is_admin = user_info.get("is_admin", False)

            if is_admin is True:
                activities = Activity.get_all(is_admin)
            else:
                allowed_buckets = PolicyManager.get_available_buckets(user_name)
                activities = Activity.get_all(is_admin, allowed_buckets)

            # Convert each Activity object to a dictionary using `to_dict()`
            return [activity.to_dict() for activity in activities]
        except Exception as e:
            logger.error(f"Error retrieving activities: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def save_activity(activity_data):
        """
        Save a new activity using the Activity model.

        Args:
            activity_data (dict): Dictionary containing the activity data.

        Returns:
            None
        """
        try:
            logger.info(
                f"Saving new activity for user {activity_data.get('userName')}."
            )
            new_activity = Activity(
                first_name=activity_data.get("firstName"),
                last_name=activity_data.get("lastName"),
                bucket_name=activity_data.get("bucketName"),
                folder_name=activity_data.get("folderName"),
                document_name=activity_data.get("documentName"),
                action=activity_data.get("action"),
                user_name=activity_data.get("userName"),
            )
            new_activity.save()
        except Exception as e:
            logger.error(f"Error saving activity: {str(e)}")
            raise e
