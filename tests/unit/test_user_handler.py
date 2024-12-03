import unittest
from unittest.mock import patch, MagicMock
import json

from aws_lambda_powertools import Logger
from app import app
from helpers.utils import DateTimeEncoder

# Ensure aws_lambda_powertools Logger is handled properly
with patch('aws_lambda_powertools.Logger', autospec=True):
    from src.handlers.user import list_users, get_user

class TestUserHandler(unittest.TestCase):
    def setUp(self):
        self.mock_logger = Logger()
        app.current_event = MagicMock()
        self.user_data = {
            "user_name": "testuser",
            "is_admin": True
        }
        self.users = [
            {"user_name": "testuser1", "is_admin": True},
            {"user_name": "testuser2", "is_admin": False}
        ]

    @patch("managers.user_manager.UserManager.get_all_users")
    def test_list_users(self, mock_get_all_users):
        mock_get_all_users.return_value = self.users

        response = list_users()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.users)

        # Test no users found scenario
        mock_get_all_users.return_value = []
        response = list_users()
        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(json.loads(response['body']), {'message': 'No users found.'})

    @patch("managers.user_manager.UserManager.get_or_create_user")
    def test_get_user(self, mock_get_or_create_user):
        app.current_event.json_body = self.user_data
        mock_get_or_create_user.return_value = self.user_data

        response = get_user()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.user_data)

        # Test missing user_name scenario
        app.current_event.json_body = {"is_admin": True}
        response = get_user()
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), {'error': 'user_name is required'})

        # Test failure to retrieve or create user
        app.current_event.json_body = self.user_data
        mock_get_or_create_user.return_value = None
        response = get_user()
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), {'error': 'Failed to retrieve or create user'})

if __name__ == "__main__":
    unittest.main()
