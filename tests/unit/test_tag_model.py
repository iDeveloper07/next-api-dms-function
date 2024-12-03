import unittest
from unittest.mock import patch, MagicMock

from src.models.tag_model import Tag

class TestTag(unittest.TestCase):
    def setUp(self):
        self.tag_data = {
            "id": 1,
            "tagkey": "Priority",
            "tagvalue": "High"
        }

    @patch('services.rds_service.RDSService.execute_query')
    @patch('helpers.common.get_tenant_id', return_value='tenant123')
    def test_get_by_id(self, mock_get_tenant_id, mock_execute_query):
        mock_execute_query.return_value = [self.tag_data]

        tag = Tag.get_by_id(1)
        self.assertIsNotNone(tag)
        self.assertIsInstance(tag, Tag)
        self.assertEqual(tag.id, 1)
        self.assertEqual(tag.tag_key, "Priority")

    @patch('services.rds_service.RDSService.execute_query')
    def test_get_by_key(self, mock_execute_query):
        mock_execute_query.return_value = [self.tag_data]

        tag = Tag.get_by_key("Priority")
        self.assertIsNotNone(tag)
        self.assertIsInstance(tag, Tag)
        self.assertEqual(tag.tag_key, "Priority")

    @patch('services.rds_service.RDSService.execute_query')
    def test_get_all(self, mock_execute_query):
        mock_execute_query.return_value = [self.tag_data]

        tags = Tag.get_all()
        self.assertEqual(len(tags), 1)
        self.assertIsInstance(tags[0], Tag)
        self.assertEqual(tags[0].tag_key, "Priority")

    @patch('services.rds_service.RDSService.execute_query')
    def test_save(self, mock_execute_query):
        tag = Tag({
            "id": 1,
            "tag_key": "Priority",
            "tag_value": "High"
        })

        tag.save()
        
        mock_execute_query.assert_called_once_with(
            "INSERT INTO Tags (tagKey, tagValue) VALUES ( %s, %s);",
            (tag.tag_key, tag.tag_value)
        )

    @patch('services.rds_service.RDSService.execute_query')
    def test_delete(self, mock_execute_query):
        Tag.delete("Priority")
        mock_execute_query.assert_called_once_with(
            "DELETE FROM Tags WHERE tagkey = %s;",
            ("Priority",)
        )

if __name__ == '__main__':
    unittest.main()
