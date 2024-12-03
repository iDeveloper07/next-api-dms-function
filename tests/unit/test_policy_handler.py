import unittest
from unittest.mock import patch, MagicMock
import json

# Import aws_lambda_powertools correctly
from aws_lambda_powertools import Logger
from app import app

# Mock aws_lambda_powertools Logger to avoid implementation specifics affecting the test environment
with patch('aws_lambda_powertools.Logger', autospec=True):
    from src.handlers.policy import policies_list, create_policy, get_user_permission, update_policy, get_allowed_buckets

class TestPolicyHandler(unittest.TestCase):
    def setUp(self):
        self.mock_logger = Logger()
        app.current_event = MagicMock()
        self.user_info = {"user_name": "test_user"}
        self.policy_data = {
            "bucket_permissions": "read",
            "policy_name": "NewPolicy",
            "user_name": "test_user"
        }
        self.policy_arn = {
            "policyArn": "arn:aws:policy/testPolicy",
            "user_name": "test_user"
        }

    @patch("managers.policy_manager.PolicyManager.list_policies")
    def test_policies_list(self, mock_list_policies):
        app.current_event.json_body = self.user_info
        mock_list_policies.return_value = ["Policy1", "Policy2"]
        
        response = policies_list()
        
        self.assertEqual(response, ["Policy1", "Policy2"])

    @patch("managers.policy_manager.PolicyManager.create_s3_policy")
    def test_create_policy(self, mock_create_s3_policy):
        app.current_event.json_body = self.policy_data
        mock_create_s3_policy.return_value = {"message": "Policy created"}

        response = create_policy()

        self.assertEqual(response, {"message": "Policy created"})

    @patch("managers.policy_manager.PolicyManager.generate_policy_input_from_existing")
    def test_get_user_permission(self, mock_generate_policy):
        app.current_event.json_body = self.policy_arn
        mock_generate_policy.return_value = {"permissions": "read"}

        response = get_user_permission()

        self.assertEqual(response, {"permissions": "read"})

    @patch("managers.policy_manager.PolicyManager.update_s3_policy")
    def test_update_policy(self, mock_update_s3_policy):
        app.current_event.json_body = {**self.policy_data, "policy_arn": "arn:aws:policy/testPolicy"}
        mock_update_s3_policy.return_value = {"message": "Policy updated"}

        response = update_policy()

        self.assertEqual(response, {"message": "Policy updated"})

    @patch("managers.policy_manager.PolicyManager.get_available_buckets")
    def test_get_allowed_buckets(self, mock_get_buckets):
        app.current_event.json_body = self.user_info
        buckets = ["bucket1", "bucket2"]
        mock_get_buckets.return_value = buckets

        response = get_allowed_buckets()
        expected_response = {"statusCode": 200, "body": json.dumps(buckets, default=str)}

        self.assertEqual(response, expected_response)

if __name__ == "__main__":
    unittest.main()
