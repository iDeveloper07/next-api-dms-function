import unittest
import re
from unittest.mock import patch
from src.models.user_model import User

class TestUser(unittest.TestCase):
    def setUp(self):
        # Mock data that matches the expected structure from the database
        self.user_data = {
            "username": "johndoe",
            "wasabiuserid": "123",
            "wasabiuserarn": "arn:aws:iam::123:user/johndoe",
            "accesskey": "AKIAIOSFODNN7EXAMPLE",
            "secretkey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "isadmin": True,
            "createdat": "2023-01-01 00:00:00"
        }

    def normalize_sql(self, sql):
        """Remove excessive whitespace from the SQL string."""
        return re.sub(r'\s+', ' ', sql).strip()
    
    @patch('services.rds_service.RDSService.execute_query')
    def test_get_all_users(self, mock_execute_query):
        # Setup mock with correct key naming
        mock_execute_query.return_value = [self.user_data]

        # Invoke the method
        users = User.get_all()

        # Assertions
        expected_sql = "SELECT userName, wasabiUserId, wasabiUserArn, accessKey, secretKey, isAdmin, createdAt FROM Users;"
        expected_sql = ' '.join(expected_sql.split())
        mock_execute_query.assert_called_once_with(expected_sql)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].user_name, 'johndoe')

    @patch('services.rds_service.RDSService.execute_query')
    def test_get_user(self, mock_execute_query):
        # Setup mock to return data with correct keys
        mock_execute_query.return_value = [self.user_data]

        # Test get user by username
        user = User.get('johndoe')

        # Assertions
        expected_sql = "SELECT wasabiUserId, wasabiUserArn, accessKey, secretKey, isAdmin, createdAt FROM Users WHERE userName = %s;"
        expected_sql = ' '.join(expected_sql.split())
        mock_execute_query.assert_called_once_with(expected_sql, ('johndoe',))

        self.assertIsNotNone(user)
        self.assertEqual(user.user_name, 'johndoe')

    @patch('services.rds_service.RDSService.execute_query')
    def test_save_user(self, mock_execute_query):
        # Setup user instance
        user = User({
            "username": "johndoe",
            "wasabiuserid": "123",
            "wasabiuserarn": "arn:aws:iam::123:user/johndoe",
            "accesskey": "AKIAIOSFODNN7EXAMPLE",
            "secretkey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "isadmin": True,
            "createdat": "2023-01-01 00:00:00"
        })

        # Test save user
        user.save()

        # Assertions
        expected_sql = """
            INSERT INTO Users (userName, wasabiUserId, wasabiUserArn, accessKey, secretKey, isAdmin)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenantId, userName) DO NOTHING;
        """

        expected_sql = self.normalize_sql(expected_sql)

        # Check the SQL query
        actual_call = mock_execute_query.call_args[0][0]
        actual_call = self.normalize_sql(actual_call)
        
        # Compare normalized SQL queries
        self.assertEqual(actual_call, expected_sql)

    @patch('services.rds_service.RDSService.execute_query')
    def test_update_user(self, mock_execute_query):
        # Setup user instance
        user = User({
            "username": "johndoe",
            "wasabiuserid": "123",
            "wasabiuserarn": "arn:aws:iam::123:user/johndoe",
            "accesskey": "AKIAIOSFODNN7EXAMPLE",
            "secretkey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "isadmin": True,
            "createdat": "2023-01-01 00:00:00"
        })

        # Test update user
        user.update()

        # Assertions
        expected_sql = """
            UPDATE Users
            SET wasabiUserId = %s, wasabiUserArn = %s, accessKey = %s, secretKey = %s, isAdmin = %s
            WHERE tenantId = %s AND userName = %s;
        """
     
        expected_sql = self.normalize_sql(expected_sql)

        # Check the SQL query
        actual_call = mock_execute_query.call_args[0][0]
        actual_call = self.normalize_sql(actual_call)
        
        # Compare normalized SQL queries
        self.assertEqual(actual_call, expected_sql)

if __name__ == '__main__':
    unittest.main()
