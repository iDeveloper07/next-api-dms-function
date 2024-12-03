import unittest
import json
from unittest.mock import patch, MagicMock
from src.managers.policy_manager import PolicyManager

class TestPolicyManager(unittest.TestCase):
    def setUp(self):
        self.user_name = "test_user"
        self.policy_name = "test_policy"
        self.policy_arn = "arn:aws:iam::aws:policy/test_policy"
        self.bucket_permissions = [
            {"bucketName": "testBucket", "canRead": True, "canWrite": False}
        ]

    @patch('boto3.client')
    @patch('managers.user_manager.UserManager.get_user_keys')
    def test_list_policies(self, mock_get_user_keys, mock_boto_client):
        # Setup mock
        mock_get_user_keys.return_value = {"accessKey": "testAccessKey", "secretKey": "testSecretKey"}
        iam_client = MagicMock()
        mock_boto_client.return_value = iam_client
        iam_client.get_paginator.return_value.paginate.return_value = [{"Policies": [{"PolicyName": "TestPolicy"}]}]
        iam_client.get_policy.return_value = {"Policy": {"PolicyName": "AdministratorAccess"}}

        # Call the function
        policies = PolicyManager.list_policies(self.user_name)
        
        # Assertions
        iam_client.get_paginator.assert_called_with("list_policies")
        self.assertIn("TestPolicy", policies)
        self.assertIn("AdministratorAccess", policies)

    @patch('boto3.client')
    @patch('managers.user_manager.UserManager.get_user_keys')
    def test_create_s3_policy(self, mock_get_user_keys, mock_boto_client):
        # Setup mock
        mock_get_user_keys.return_value = {"accessKey": "testAccessKey", "secretKey": "testSecretKey"}
        iam_client = MagicMock()
        mock_boto_client.return_value = iam_client
        iam_client.create_policy.return_value = {"Policy": {"PolicyName": self.policy_name}}

        # Call the function
        result = PolicyManager.create_s3_policy(self.bucket_permissions, self.policy_name, self.user_name)
        
        # Assertions
        self.assertEqual(result, {"statusCode": 200, "body": "Role created successfully"})
        iam_client.create_policy.assert_called_once()

    @patch('boto3.client')
    @patch('managers.user_manager.UserManager.get_user_keys')
    def test_get_bucket_permissions_from_policy(self, mock_get_user_keys, mock_boto_client):
        # Setup mock
        mock_get_user_keys.return_value = {"accessKey": "testAccessKey", "secretKey": "testSecretKey"}
        iam_client = MagicMock()
        mock_boto_client.return_value = iam_client
        iam_client.get_policy.return_value = {"Policy": {"PolicyName": self.policy_name}}

        # Define a fake policy document
        policy_document = {
            "Statement": [
                {"Effect": "Allow", "Action": ["s3:ListBucket", "s3:GetObject"], "Resource": "arn:aws:s3:::testBucket/*"}
            ]
        }

        # Call the function
        permissions = PolicyManager.get_bucket_permissions_from_policy(policy_document, [{"Name": "testBucket"}])
        
        # Assertions
        self.assertTrue(permissions[0]["canRead"])
        self.assertFalse(permissions[0]["canWrite"])


    @patch('managers.user_manager.UserManager.get_user_keys')
    @patch('managers.tenant_manager.TenantManager.get_tenant_keys')
    @patch('boto3.client')
    def test_get_available_buckets(self, mock_boto_client, mock_get_tenant_keys, mock_get_user_keys):
        # Prepare mock data for the user and tenant keys
        mock_get_tenant_keys.return_value = {"accessKey": "tenantAccessKey", "secretKey": "tenantSecretKey"}
        mock_get_user_keys.return_value = {"accessKey": "userAccessKey", "secretKey": "userSecretKey"}

        # Mock IAM client behavior
        iam_client = MagicMock()
        mock_boto_client.return_value = iam_client
        iam_client.list_attached_user_policies.return_value = {"AttachedPolicies": [{"PolicyArn": self.policy_arn}]}
        iam_client.get_policy.return_value = {"Policy": {"DefaultVersionId": "v1"}}
        iam_client.get_policy_version.return_value = {
            "PolicyVersion": {
                "Document": {
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:ListBucket"],
                            "Resource": "arn:aws:s3:::example-bucket"
                        }
                    ]
                }
            }
        }

        # Execute the method
        buckets = PolicyManager.get_available_buckets(self.user_name)

        # Verify the results
        self.assertIn("example-bucket", buckets)
        mock_get_tenant_keys.assert_called_once()

if __name__ == '__main__':
    unittest.main()
