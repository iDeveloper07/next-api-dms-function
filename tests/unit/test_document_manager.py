import unittest
from unittest.mock import patch, MagicMock

from src.managers.document_manager import DocumentManager

class TestDocumentManager(unittest.TestCase):
    def setUp(self):
        self.document_data = {
            "bucketName": "bucket1",
            "name": "TestDoc",
            "key": "testdoc.pdf",
            "prefix": "test/",
            "size": 1024,
            "type": "pdf",
            "hash": "abcd1234",
            "version": "1"
        }
        self.document_id = 1
        self.tag_key = "Important"
        self.documents = [MagicMock(to_dict=lambda: {"id": 1, "name": "TestDoc"})]

    @patch('models.document_model.Document.get_all')
    def test_get_all_documents(self, mock_get_all):
        mock_get_all.return_value = self.documents
        documents = DocumentManager.get_all_documents()
        self.assertEqual(documents, [{"id": 1, "name": "TestDoc"}])
        mock_get_all.assert_called_once()

    @patch('models.document_model.Document.get_by_id')
    def test_get_document(self, mock_get_by_id):
        mock_document = MagicMock(to_dict=lambda: self.document_data)
        mock_get_by_id.return_value = mock_document
        document = DocumentManager.get_document(self.document_id)
        self.assertEqual(document, self.document_data)
        mock_get_by_id.assert_called_with(self.document_id)

    @patch('models.document_model.Document.get_documents_by_tag')
    def test_get_documents_by_tag(self, mock_get_documents_by_tag):
        mock_get_documents_by_tag.return_value = self.documents
        documents = DocumentManager.get_documents_by_tag(self.tag_key)
        self.assertEqual(documents, [{"id": 1, "name": "TestDoc"}])
        mock_get_documents_by_tag.assert_called_with(self.tag_key)

    @patch('models.document_model.Document.get_by_id')
    def test_update_document(self, mock_get_by_id):
        mock_document = MagicMock(update=MagicMock(return_value=True))
        mock_get_by_id.return_value = mock_document
        result = DocumentManager.update_document(self.document_id, self.document_data)
        self.assertTrue(result)
        mock_get_by_id.assert_called_with(self.document_id)
        mock_document.update.assert_called_with(self.document_data)

    @patch('models.document_model.Document.get_by_id')
    def test_delete_document(self, mock_get_by_id):
        mock_document = MagicMock(delete=MagicMock())
        mock_get_by_id.return_value = mock_document
        result = DocumentManager.delete_document(self.document_id)
        self.assertTrue(result)
        mock_document.delete.assert_called_once()

    @patch('models.document_model.Document.get_by_key')
    def test_get_document_by_key(self, mock_get_by_key):
        mock_document = MagicMock(to_dict=lambda: self.document_data)
        mock_get_by_key.return_value = mock_document
        result = DocumentManager.get_document_by_key({"key": "testdoc.pdf", "version": "1"})
        self.assertEqual(result, self.document_data)
        mock_get_by_key.assert_called_once()

    @patch('models.document_model.Document.get_documents_by_name_tag')
    def test_search_documents(self, mock_search_documents):
        mock_search_documents.return_value = self.documents
        result = DocumentManager.search_documents({"name": "TestDoc", "tag": "Important"})
        self.assertEqual(result, [{"id": 1, "name": "TestDoc"}])
        mock_search_documents.assert_called_once()


    @patch('models.document_model.Document.save')
    @patch('models.document_model.Document.__init__', return_value=None)  # Mock the constructor
    @patch('helpers.common.get_tenant_id', return_value='fake_tenant_id')
    def test_save_document(self, mock_get_tenant_id, mock_document_init, mock_save):
        mock_document_class = MagicMock()
        mock_document_class.return_value = mock_document_class

        DocumentManager.save_document(self.document_data)

        mock_document_init.assert_called_once_with(
            bucket_name=self.document_data['bucketName'],
            name=self.document_data['name'],
            key=self.document_data['key'],
            prefix=self.document_data['prefix'],
            size=self.document_data['size'],
            type=self.document_data['type'],
            hash=self.document_data['hash'],
            version=self.document_data['version'],
        )

        mock_save.assert_called_once()
        
if __name__ == '__main__':
    unittest.main()
