import unittest
from unittest.mock import patch, MagicMock

from src.managers.user_manager import UserManager

class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.user_data = {
            "userName": "testUser",
            "userId": "wasabi123",
            "userArn": "arn:aws:iam::123456789012:user/testUser",
            "accessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "secretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "isAdmin": False
        }
        self.user_name = "testUser"
        self.is_admin = False

    @patch('models.user_model.User.get_all')
    def test_get_all_users(self, mock_get_all):
        mock_user_instance = MagicMock()
        mock_user_instance.to_dict.return_value = self.user_data
        mock_get_all.return_value = [mock_user_instance]
        
        users = UserManager.get_all_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0], self.user_data)
        mock_get_all.assert_called_once()

    @patch('managers.tenant_manager.TenantManager.get_tenant_keys')
    @patch('services.wasabi_service.WasabiService.create_wasabi_subuser')
    @patch('models.user_model.User.get')
    def test_get_or_create_user(self, mock_create_user, mock_create_wasabi_subuser, mock_get_tenant_keys):
        mock_get_tenant_keys.return_value = {"accessKey": "ACCESS123", "secretKey": "SECRET123"}
        mock_create_wasabi_subuser.return_value = self.user_data
        mock_create_user.return_value = MagicMock(to_dict=lambda: self.user_data)

        user = UserManager.get_or_create_user(self.user_name, self.is_admin)
        self.assertEqual(user, self.user_data)
        mock_create_user.assert_called_once()

    @patch('models.user_model.User.get')
    def test_get_user(self, mock_get_user):
        mock_user_instance = MagicMock()
        mock_user_instance.to_dict.return_value = self.user_data
        mock_get_user.return_value = mock_user_instance
        
        user = UserManager.get_user(self.user_name)
        self.assertEqual(user, mock_user_instance)
        mock_get_user.assert_called_once_with(self.user_name)

    @patch('models.user_model.User.save')
    def test_create_user(self, mock_save):
        mock_user_instance = MagicMock()
        mock_user_instance.save.return_value = None
        
        UserManager.create_user(self.user_data)
        mock_save.assert_called_once()

    @patch('models.user_model.User.get')
    def test_get_user_keys(self, mock_get_user):
        mock_user_instance = MagicMock(access_key="ACCESS123", secret_key="SECRET123")
        mock_get_user.return_value = mock_user_instance
        
        keys = UserManager.get_user_keys(self.user_name)
        self.assertEqual(keys, {"accessKey": "ACCESS123", "secretKey": "SECRET123"})
        mock_get_user.assert_called_once_with(self.user_name)

if __name__ == '__main__':
    unittest.main()
