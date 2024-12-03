import unittest
from unittest.mock import patch, MagicMock
import json

from aws_lambda_powertools import Logger
from app import app

# Ensure aws_lambda_powertools Logger is handled properly
with patch('aws_lambda_powertools.Logger', autospec=True):
    from src.handlers.tenant import create_tenant, run_sql_script, execute_custom_sql

class TestTenantHandler(unittest.TestCase):
    def setUp(self):
        self.mock_logger = Logger()
        app.current_event = MagicMock()
        self.tenant_data = {
            "account_name": "ExampleTenant",
            "seed_user_id": "user123"
        }
        self.sql_data = {
            "query": "SELECT * FROM users;"
        }

    @patch("managers.tenant_manager.TenantManager.create_tenant")
    @patch("managers.user_manager.UserManager.get_or_create_user")
    def test_create_tenant(self, mock_get_or_create_user, mock_create_tenant):
        app.current_event.json_body = self.tenant_data
        mock_create_tenant.return_value = MagicMock(tenant_id='1')
        mock_get_or_create_user.return_value = {"userName": "user123"}

        response = create_tenant()

        self.assertEqual(response['statusCode'], 201)
        self.assertTrue('Tenant 1 created successfully' in json.loads(response['body'])['message'])

    @patch("services.rds_service.RDSService.execute_query")
    def test_run_sql_script(self, mock_execute_query):
        mock_execute_query.return_value = None

        response = run_sql_script()

        self.assertEqual(response['statusCode'], 200)
        self.assertTrue('SQL script executed successfully' in json.loads(response['body'])['message'])

    @patch("services.rds_service.RDSService.execute_query")
    def test_execute_custom_sql(self, mock_execute_query):
        app.current_event.json_body = self.sql_data
        mock_execute_query.return_value = [{"id": 1, "name": "John Doe"}]

        response = execute_custom_sql()

        self.assertEqual(response['statusCode'], 200)
        result = json.loads(response['body'])
        self.assertEqual(result['result'][0]['name'], "John Doe")

if __name__ == "__main__":
    unittest.main()
