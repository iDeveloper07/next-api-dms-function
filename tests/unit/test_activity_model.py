import unittest
from unittest.mock import patch, MagicMock

from src.models.activity_model import Activity

class TestActivity(unittest.TestCase):
    def setUp(self):
        self.activity_data = {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "bucket_name": "main_bucket",
            "folder_name": "folder2023",
            "document_name": "file.pdf",
            "action": "upload",
            "user_name": "johndoe",
            "time_stamp": "2023-10-02 12:00:00"
        }
        self.allowed_buckets = ["main_bucket", "secondary_bucket"]

    @patch('services.rds_service.RDSService.execute_query')
    @patch('helpers.common.get_tenant_id', return_value='tenant123')
    def test_get_all(self, mock_get_tenant_id, mock_execute_query):
        # Adjust this mock return to align with expected database output
        mock_execute_query.return_value = [{
            "id": 1,
            "firstname": "John",
            "lastname": "Doe",
            "bucketname": "main_bucket",
            "foldername": "folder2023",
            "documentname": "file.pdf",
            "action": "upload",
            "username": "johndoe",
            "timestamp": "2023-10-02 12:00:00"
        }]

        activities = Activity.get_all(is_admin=True, allowed_buckets=self.allowed_buckets)
        self.assertEqual(len(activities), 1)
        self.assertIsInstance(activities[0], Activity)
        self.assertEqual(activities[0].first_name, "John")

    @patch('services.rds_service.RDSService.execute_query')
    @patch('helpers.common.get_tenant_id', return_value='tenant123')
    def test_save(self, mock_get_tenant_id, mock_execute_query):
        activity = Activity(**self.activity_data)
        activity.save()

        # Ensure the SQL query and parameters are correctly constructed and passed
        mock_execute_query.assert_called_once_with(
            "INSERT INTO Activity (firstName, lastName, bucketName, folderName, documentName, action, userName) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s);",
            (activity.first_name, activity.last_name, activity.bucket_name, activity.folder_name, activity.document_name, activity.action, activity.user_name)
        )

if __name__ == '__main__':
    unittest.main()
