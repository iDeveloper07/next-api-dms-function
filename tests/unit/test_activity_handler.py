import unittest
from unittest.mock import patch, MagicMock
import json

from aws_lambda_powertools import Logger
from app import app

# Ensure aws_lambda_powertools Logger is handled properly
with patch('aws_lambda_powertools.Logger', autospec=True):
    from src.handlers.activity import get_activities, save_activity

class TestActivityHandler(unittest.TestCase):
    def setUp(self):
        self.mock_logger = Logger()
        app.current_event = MagicMock()
        self.activity_data = {
            "firstName": "John",
            "lastName": "Doe",
            "bucketName": "bucket1",
            "action": "CREATE",
            "userName": "john.doe"
        }
        self.user_info = {"user_name": "john.doe"}
        self.activities_list = [
            {"firstName": "John", "lastName": "Doe", "bucketName": "bucket1", "action": "CREATE", "userName": "john.doe"}
        ]

    @patch("managers.activity_manager.ActivityManager.get_all_activities")
    def test_get_activities(self, mock_get_all_activities):
        app.current_event.json_body = self.user_info
        mock_get_all_activities.return_value = self.activities_list

        response = get_activities()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.activities_list)

    @patch("managers.activity_manager.ActivityManager.save_activity")
    def test_save_activity(self, mock_save_activity):
        app.current_event.json_body = self.activity_data
        mock_save_activity.return_value = None

        response = save_activity()

        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(json.loads(response['body']), {'message': 'Activity saved successfully'})

        # Test missing required fields
        incomplete_data = {
            "firstName": "John",
            "bucketName": "bucket1",
            "action": "CREATE",
        }
        app.current_event.json_body = incomplete_data
        response = save_activity()
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), {'error': 'Missing required fields'})

if __name__ == "__main__":
    unittest.main()
