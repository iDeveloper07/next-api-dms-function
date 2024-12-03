import unittest
import re
from unittest.mock import patch, MagicMock

from src.models.tenant_model import Tenant

class TestTenant(unittest.TestCase):
    def setUp(self):
        self.tenant_data = {
            "wasabi_sub_account_num": "123456",
            "wasabi_sub_account_name": "TestTenant",
            "password": "password123",
            "access_key": "testAccessKey",
            "secret_key": "testSecretKey"
        }


    def normalize_sql(self, sql):
        """Remove excessive whitespace from the SQL string."""
        return re.sub(r'\s+', ' ', sql).strip()


    @patch('services.rds_service.RDSService.execute_query')
    @patch('helpers.common.get_tenant_id', return_value='tenant123')
    def test_save(self, mock_get_tenant_id, mock_execute_query):
        tenant = Tenant(**self.tenant_data)
        tenant.save()

        expected_sql = """
            INSERT INTO Tenants (wasabiSubAccountNum, wasabiSubAccountName, password, accessKey, secretKey)
            VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s, %s)
            ON CONFLICT (tenantId, wasabiSubAccountNum) DO NOTHING;
        """
        # Normalize SQL
        expected_sql = self.normalize_sql(expected_sql)

        # Check the SQL query
        actual_call = mock_execute_query.call_args[0][0]
        actual_call = self.normalize_sql(actual_call)
        
        # Compare normalized SQL queries
        self.assertEqual(actual_call, expected_sql)

    @patch('services.rds_service.RDSService.execute_query')
    @patch('helpers.common.get_tenant_id', return_value='tenant123')
    def test_get_tenant_keys(self, mock_get_tenant_id, mock_execute_query):
        mock_execute_query.return_value = [{
            "accesskey": "testAccessKey",
            "secretkey": "testSecretKey"
        }]
        
        tenant = Tenant.get_tenant_keys()
        self.assertEqual(tenant.access_key, "testAccessKey")
        self.assertEqual(tenant.secret_key, "testSecretKey")

if __name__ == '__main__':
    unittest.main()
