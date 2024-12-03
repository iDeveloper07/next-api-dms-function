import unittest
from unittest.mock import patch, MagicMock
import json

from aws_lambda_powertools import Logger
from app import app

# Ensure aws_lambda_powertools Logger is handled properly
with patch('aws_lambda_powertools.Logger', autospec=True):
    from src.handlers.document import get_documents, get_document, create_document, update_document, delete_document, get_documents_by_tag, search_document, get_document_by_key, delete_documents

class TestDocumentHandler(unittest.TestCase):
    def setUp(self):
        self.mock_logger = Logger()
        app.current_event = MagicMock()
        self.document_data = {
            "bucketName": "bucket1",
            "name": "TestDoc",
            "key": "testdoc.pdf",
            "size": 1024,
            "hash": "abcd1234",
            "version": "1"
        }
        self.document_id = "1"
        self.tag_key = "Important"
        self.documents_list = [self.document_data]

    @patch("managers.document_manager.DocumentManager.get_all_documents")
    def test_get_documents(self, mock_get_all_documents):
        mock_get_all_documents.return_value = self.documents_list

        response = get_documents()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.documents_list)

    @patch("managers.document_manager.DocumentManager.get_document")
    def test_get_document(self, mock_get_document):
        mock_get_document.return_value = self.document_data

        response = get_document(self.document_id)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.document_data)

    @patch("managers.document_manager.DocumentManager.save_document")
    def test_create_document(self, mock_save_document):
        app.current_event.json_body = self.document_data
        mock_save_document.return_value = None

        response = create_document()

        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(json.loads(response['body']), {'message': 'Document created successfully'})

    @patch("managers.document_manager.DocumentManager.update_document", return_value=True)
    def test_update_document(self, mock_update_document):
        app.current_event.json_body = self.document_data

        response = update_document(self.document_id)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'message': 'Document updated successfully'})

    @patch("managers.document_manager.DocumentManager.delete_document", return_value=True)
    def test_delete_document(self, mock_delete_document):
        response = delete_document(self.document_id)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'message': 'Document deleted successfully'})

    @patch("managers.document_manager.DocumentManager.get_documents_by_tag")
    def test_get_documents_by_tag(self, mock_get_documents_by_tag):
        mock_get_documents_by_tag.return_value = self.documents_list

        response = get_documents_by_tag(self.tag_key)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.documents_list)

    @patch("managers.document_manager.DocumentManager.search_documents")
    def test_search_document(self, mock_search_documents):
        app.current_event.json_body = {"bucketName": "bucket1"}
        mock_search_documents.return_value = self.documents_list

        response = search_document()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.documents_list)

    @patch("managers.document_manager.DocumentManager.get_document_by_key")
    def test_get_document_by_key(self, mock_get_document_by_key):
        app.current_event.json_body = self.document_data
        mock_get_document_by_key.return_value = self.document_data

        response = get_document_by_key()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.document_data)

    @patch("managers.document_manager.DocumentManager.delete_documents", return_value=True)
    def test_delete_documents(self, mock_delete_documents):
        app.current_event.json_body = {"bucketName": "bucket1", "type": "file"}
        response = delete_documents()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'message': 'Document deleted successfully'})

if __name__ == "__main__":
    unittest.main()
