import unittest
from unittest.mock import patch, MagicMock

from src.managers.tenant_manager import TenantManager

class TestTenantManager(unittest.TestCase):
    def setUp(self):
        self.tenant_data = {
            "account_name": "testTenant",
            "quota": 1024,
            "isTrial": True,
            "enableFtp": False
        }
        self.wasabi_account_details = {
            "account_number": "123456",
            "account_name": "testTenant",
            "password": "pass1234",
            "access_key": "testAccessKey",
            "secret_key": "testSecretKey"
        }

    @patch('services.wasabi_service.WasabiService.create_wasabi_subaccount')
    @patch('models.tenant_model.Tenant.save')
    @patch('models.tenant_model.Tenant.__init__', return_value=None)  # Mock the constructor of the Tenant model
    def test_create_tenant(self, mock_tenant_init, mock_save, mock_create_wasabi_subaccount):
        mock_create_wasabi_subaccount.return_value = self.wasabi_account_details
        TenantManager.create_tenant(self.tenant_data)
        
        mock_create_wasabi_subaccount.assert_called_once_with("testTenant", 1024, True, False)
        mock_save.assert_called_once()
        mock_tenant_init.assert_called_once_with(
            wasabi_sub_account_num='123456',
            wasabi_sub_account_name='testTenant',
            password='pass1234',
            access_key='testAccessKey',
            secret_key='testSecretKey'
        )

    @patch('models.tenant_model.Tenant.get_tenant_keys')
    @patch('helpers.common.get_tenant_id', return_value='123456')
    def test_get_tenant_keys(self, mock_get_tenant_id, mock_get_tenant_keys):
        mock_tenant_instance = MagicMock(access_key='testAccessKey', secret_key='testSecretKey')
        mock_get_tenant_keys.return_value = mock_tenant_instance
        
        tenant_keys = TenantManager.get_tenant_keys()
        
        self.assertEqual(tenant_keys, {"accessKey": "testAccessKey", "secretKey": "testSecretKey"})
        mock_get_tenant_keys.assert_called_once()

if __name__ == '__main__':
    unittest.main()
