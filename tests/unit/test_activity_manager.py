import unittest
from unittest.mock import patch, MagicMock

from src.managers.activity_manager import ActivityManager

class TestActivityManager(unittest.TestCase):
    def setUp(self):
        self.user_info_admin = {"user_name": "admin_user", "is_admin": True}
        self.user_info_user = {"user_name": "regular_user", "is_admin": False}
        self.activity_data = {
            "firstName": "John",
            "lastName": "Doe",
            "bucketName": "TestBucket",
            "folderName": "TestFolder",
            "documentName": "TestDocument",
            "action": "create",
            "userName": "JohnDoe"
        }
        self.activities = [MagicMock(to_dict=lambda: {"id": 1, "name": "Hiking"})]

    @patch('src.managers.activity_manager.Activity.get_all')
    @patch('src.managers.activity_manager.PolicyManager.get_available_buckets')
    def test_get_all_activities_admin(self, mock_get_available_buckets, mock_get_all):
        # Setup mocks
        mock_get_all.return_value = self.activities

        # Create an instance of the manager
        manager = ActivityManager()
        result = manager.get_all_activities(self.user_info_admin)

        # Verify the behavior
        mock_get_all.assert_called_once_with(True)
        self.assertEqual(result, [{"id": 1, "name": "Hiking"}])

    @patch('src.managers.activity_manager.Activity.get_all')
    @patch('src.managers.activity_manager.PolicyManager.get_available_buckets')
    def test_get_all_activities_regular_user(self, mock_get_available_buckets, mock_get_all):
        # Setup mocks
        mock_get_available_buckets.return_value = ["TestBucket"]
        mock_get_all.return_value = self.activities

        # Create an instance of the manager
        manager = ActivityManager()
        result = manager.get_all_activities(self.user_info_user)

        # Verify the behavior
        mock_get_available_buckets.assert_called_once_with("regular_user")
        mock_get_all.assert_called_once_with(False, ["TestBucket"])
        self.assertEqual(result, [{"id": 1, "name": "Hiking"}])

    @patch('src.managers.activity_manager.Activity')
    def test_save_activity(self, mock_activity_class):
        # Setup the mock for the Activity class
        mock_activity_instance = MagicMock()
        mock_activity_class.return_value = mock_activity_instance

        # Create an instance of the manager
        manager = ActivityManager()
        manager.save_activity(self.activity_data)

        # Verify the behavior
        mock_activity_class.assert_called_once_with(
            first_name="John",
            last_name="Doe",
            bucket_name="TestBucket",
            folder_name="TestFolder",
            document_name="TestDocument",
            action="create",
            user_name="JohnDoe"
        )
        mock_activity_instance.save.assert_called_once()

if __name__ == '__main__':
    unittest.main()
