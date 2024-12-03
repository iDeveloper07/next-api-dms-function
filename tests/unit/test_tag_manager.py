import unittest
from unittest.mock import patch, MagicMock, call

from src.managers.tag_manager import TagManager


class TestTagManager(unittest.TestCase):
    def setUp(self):
        self.tag_data = {"tagKey": "Environment", "tagValue": "Production"}
        self.document_tag_data = {
            "bucketName": "example_bucket",
            "documentId": 1,
            "tags": [{"Key": "Environment"}],
        }
        self.tag_key = "Environment"
        self.document_id = 1

    @patch("models.tag_model.Tag.get_all")
    def test_get_all_tags(self, mock_get_all):
        mock_tag = MagicMock()
        mock_tag.to_dict.return_value = self.tag_data
        mock_get_all.return_value = [mock_tag]

        tags = TagManager.get_all_tags()
        self.assertEqual(tags, [self.tag_data])
        mock_get_all.assert_called_once()

    @patch("models.tag_model.Tag.get_by_key")
    def test_get_tag_by_key(self, mock_get_by_key):
        mock_tag = MagicMock()
        mock_tag.to_dict.return_value = self.tag_data
        mock_get_by_key.return_value = mock_tag

        tag = TagManager.get_tag_by_key(self.tag_key)
        self.assertEqual(tag, self.tag_data)
        mock_get_by_key.assert_called_with(self.tag_key)

    @patch("models.tag_model.DocumentTag.get_tags_for_document")
    def test_get_tags_for_document(self, mock_get_tags_for_document):
        mock_tag = MagicMock()
        mock_tag.to_dict.return_value = {"tagKey": "Environment"}
        mock_get_tags_for_document.return_value = [mock_tag]

        tags = TagManager.get_tags_for_document(self.document_id)
        self.assertEqual(tags, [{"tagKey": "Environment"}])
        mock_get_tags_for_document.assert_called_with(self.document_id)

    @patch("models.tag_model.Tag.save")
    @patch(
        "models.tag_model.Tag.__init__", return_value=None
    )  # Mock the constructor to not perform any actions
    def test_save_tag(self, mock_init, mock_save):
        # Initialize a MagicMock for the Tag class to use as an instance
        mock_tag_instance = MagicMock()

        # Assigning the mock instance to the class
        with patch("models.tag_model.Tag", return_value=mock_tag_instance):
            # Call the method under test
            TagManager.save_tag(self.tag_data)

            # Check that the constructor was called correctly with provided data
            mock_init.assert_called_once_with(
                tag_key=self.tag_data["tagKey"], tag_value=self.tag_data["tagValue"]
            )

    @patch("models.tag_model.Tag.exists_by_key")
    def test_check_tag_exists(self, mock_exists_by_key):
        mock_exists_by_key.return_value = True

        exists = TagManager.check_tag_exists(self.tag_key)
        self.assertTrue(exists)
        mock_exists_by_key.assert_called_with(self.tag_key)

    @patch("models.tag_model.DocumentTag.save")
    @patch(
        "models.tag_model.DocumentTag.__init__", return_value=None
    )  # Mock the constructor to not perform any actions
    def test_save_document_tag(self, mock_init, mock_save):
        # Set up a mock instance for DocumentTag to be used in each creation
        mock_document_tag_instance = MagicMock()
        with patch(
            "models.tag_model.DocumentTag", return_value=mock_document_tag_instance
        ):
            # Call the method under test
            TagManager.save_document_tag(self.document_tag_data)

            # Check that the constructor was called correctly for each tag
            expected_calls = [
                call(
                    bucket_name=self.document_tag_data["bucketName"],
                    document_id=self.document_tag_data["documentId"],
                    tag_key=tag["Key"],
                )
                for tag in self.document_tag_data["tags"]
            ]
            mock_init.assert_has_calls(expected_calls, any_order=True)

            # Ensure the save method was called on each instance
            self.assertEqual(mock_save.call_count, len(self.document_tag_data["tags"]))

    @patch("models.tag_model.Tag.delete")
    @patch("models.tag_model.DocumentTag.is_tag_associated")
    def test_delete_tag(self, mock_is_tag_associated, mock_delete):
        mock_is_tag_associated.return_value = False

        result = TagManager.delete_tag(self.tag_key)
        self.assertTrue(result)
        mock_delete.assert_called_once_with(self.tag_key)

    @patch("models.tag_model.DocumentTag.get_association")
    def test_delete_document_tag(self, mock_get_association):
        mock_association = MagicMock()
        mock_get_association.return_value = mock_association

        result = TagManager.delete_document_tag(self.document_tag_data)
        mock_get_association.assert_called_once()
        mock_association.delete.assert_called_once()


if __name__ == "__main__":
    unittest.main()
