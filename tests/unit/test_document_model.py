import unittest
from unittest.mock import patch, MagicMock
from src.models.document_model import Document

class TestDocument(unittest.TestCase):
    def setUp(self):
        self.document_data = {
            "id": 1,
            "bucket_name": "TestBucket",
            "name": "TestDocument",
            "key": "TestKey",
            "prefix": "TestPrefix",
            "size": 1024,
            "type": "PDF",
            "hash": "abcd1234",
            "version": "v1",
            "created_at": "2023-01-01 00:00:00"
        }

    @patch('services.rds_service.RDSService.execute_query')
    @patch('helpers.common.get_tenant_id', return_value='tenant123')
    def test_get_all(self, mock_get_tenant_id, mock_execute_query):
        # Setup the mock to return appropriate database row format
        mock_execute_query.return_value = [{
            "id": 1,
            "bucketname": "TestBucket",
            "name": "TestDocument",
            "key": "TestKey",
            "prefix": "TestPrefix",
            "size": 1024,
            "type": "PDF",
            "hash": "abcd1234",
            "version": "v1",
            "createdat": "2023-01-01 00:00:00"
        }]
        documents = Document.get_all()
        self.assertEqual(len(documents), 1)
        self.assertIsInstance(documents[0], Document)
        self.assertEqual(documents[0].name, "TestDocument")
        mock_execute_query.assert_called_once_with("SELECT * FROM Documents;")

    @patch('services.rds_service.RDSService.execute_query')
    @patch('helpers.common.get_tenant_id', return_value='tenant123')
    def test_get_by_id(self, mock_get_tenant_id, mock_execute_query):
        mock_execute_query.return_value = [{
            "id": 1,
            "bucketname": "TestBucket",
            "name": "TestDocument",
            "key": "TestKey",
            "prefix": "TestPrefix",
            "size": 1024,
            "type": "PDF",
            "hash": "abcd1234",
            "version": "v1",
            "createdat": "2023-01-01 00:00:00"
        }]
        
        document = Document.get_by_id(1)
        self.assertIsInstance(document, Document)
        self.assertEqual(document.id, 1)
        mock_execute_query.assert_called_once_with("SELECT * FROM Documents WHERE id = %s;", (1,))

    @patch('services.rds_service.RDSService.execute_query')
    @patch('helpers.common.get_tenant_id', return_value='tenant123')
    def test_save(self, mock_get_tenant_id, mock_execute_query):
        document = Document(**self.document_data)
        document.save()
        
        mock_execute_query.assert_called_once_with(
            "INSERT INTO Documents (bucketName, name, key, prefix, size, type, hash, version) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
            (document.bucket_name, document.name, document.key, document.prefix, document.size, document.type, document.hash, document.version)
        )

    @patch('services.rds_service.RDSService.execute_query')
    @patch('helpers.common.get_tenant_id', return_value='tenant123')
    def test_update(self, mock_get_tenant_id, mock_execute_query):
        document = Document(**self.document_data)
        update_data = {
            "name": "UpdatedName",
            "type": "TXT"
        }
        document.update(update_data)
        
        mock_execute_query.assert_called_once_with(
            "UPDATE Documents SET bucketName = %s, name = %s, key = %s, prefix = %s, size = %s, type = %s, hash = %s, version = %s WHERE id = %s;",
            (document.bucket_name, "UpdatedName", document.key, document.prefix, document.size, "TXT", document.hash, document.version, document.id)
        )

if __name__ == '__main__':
    unittest.main()
