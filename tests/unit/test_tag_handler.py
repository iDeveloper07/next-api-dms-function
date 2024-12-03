import unittest
from unittest.mock import patch, MagicMock
import json

from aws_lambda_powertools import Logger
from app import app

# Ensure aws_lambda_powertools Logger is handled properly
with patch('aws_lambda_powertools.Logger', autospec=True):
    from src.handlers.tag import create_tag, get_tags, get_tag, delete_tag, create_document_tag, get_document_tags, delete_document_tag

class TestTagHandler(unittest.TestCase):
    def setUp(self):
        self.mock_logger = Logger()
        app.current_event = MagicMock()
        self.tag_data = {
            "tagKey": "ExampleKey",
            "tagValue": "ExampleValue"
        }
        self.document_tag_data = {
            "bucketName": "example-bucket",
            "documentId": "123",
            "tags": ["tag1", "tag2"]
        }
        self.tag_key = "ExampleKey"
        self.document_id = "123"

    @patch("managers.tag_manager.TagManager.check_tag_exists", return_value=False)
    @patch("managers.tag_manager.TagManager.save_tag")
    def test_create_tag(self, mock_save_tag, mock_check_tag_exists):
        app.current_event.json_body = self.tag_data
        mock_save_tag.return_value = None

        response = create_tag()

        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(json.loads(response['body']), {'message': 'Tag created successfully'})

    @patch("managers.tag_manager.TagManager.get_all_tags")
    def test_get_tags(self, mock_get_all_tags):
        mock_get_all_tags.return_value = [self.tag_data]

        response = get_tags()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), [self.tag_data])

    @patch("managers.tag_manager.TagManager.get_tag_by_key")
    def test_get_tag(self, mock_get_tag_by_key):
        mock_get_tag_by_key.return_value = self.tag_data

        response = get_tag(self.tag_key)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.tag_data)

    @patch("managers.tag_manager.TagManager.delete_tag", return_value=True)
    def test_delete_tag(self, mock_delete_tag):
        response = delete_tag(self.tag_key)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'message': 'Tag deleted successfully'})

    @patch("managers.tag_manager.TagManager.save_document_tag")
    def test_create_document_tag(self, mock_save_document_tag):
        app.current_event.json_body = self.document_tag_data
        mock_save_document_tag.return_value = None

        response = create_document_tag()

        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(json.loads(response['body']), {'message': 'Document tag association created successfully'})

    @patch("managers.tag_manager.TagManager.get_tags_for_document")
    def test_get_document_tags(self, mock_get_tags_for_document):
        mock_get_tags_for_document.return_value = [self.tag_data]

        response = get_document_tags(self.document_id)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), [self.tag_data])

    @patch("managers.tag_manager.TagManager.delete_document_tag", return_value=True)
    def test_delete_document_tag(self, mock_delete_document_tag):
        app.current_event.json_body = self.document_tag_data
        response = delete_document_tag()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'message': 'Document tag association deleted successfully'})

if __name__ == "__main__":
    unittest.main()
