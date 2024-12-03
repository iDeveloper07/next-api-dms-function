import unittest
from unittest.mock import patch, MagicMock
from src.managers.workflow_manager import WorkflowManager

class TestWorkflowManager(unittest.TestCase):
    def setUp(self):
        self.workflow_data = {
            "id" : 1,
            "triggerName": "TriggerA",
            "projectName": "ProjectA",
            "workflowId": "WF001",
            "bucketName": "BucketA",
            "folderPath": "FolderA",
            "action": "CREATE"  # Ensure this is a valid enum value in your model
        }
        self.workflow = MagicMock()
        self.workflow.to_dict.return_value = self.workflow_data
        self.workflow_id = 1

    @patch('models.workflow_model.Workflow.get_all')
    def test_get_all_workflows(self, mock_get_all):
        mock_get_all.return_value = [self.workflow]
        results = WorkflowManager.get_all_workflows()
        self.assertEqual(results, [self.workflow.to_dict()])
        mock_get_all.assert_called_once()

    @patch('models.workflow_model.Workflow.save')
    @patch('models.workflow_model.Workflow.__init__', return_value=None)  # Ensure constructor does not perform its original function
    def test_save_workflow(self, mock_init, mock_save):
        # Mock the Workflow class itself to control instantiation behavior
        with patch('models.workflow_model.Workflow') as mock_workflow_class:
            mock_workflow_instance = MagicMock()
            mock_workflow_class.return_value = mock_workflow_instance
            
            # Call the method under test
            WorkflowManager.save_workflow(self.workflow_data)
            
            # Validate that the Workflow constructor was called correctly
            mock_init.assert_called_once_with(
                triggerName='TriggerA',
                projectName='ProjectA',
                workflowId='WF001',
                bucketName='BucketA',
                folderPath='FolderA',
                action='CREATE'
            )
            
    @patch('models.workflow_model.Workflow.get_by_id')
    @patch('models.workflow_model.Workflow.update')
    def test_update_workflow(self, mock_update, mock_get_by_id):
        mock_get_by_id.return_value = self.workflow
        result = WorkflowManager.update_workflow({"id": self.workflow_id, **self.workflow_data})
        self.assertTrue(result)
        mock_get_by_id.assert_called_once_with(self.workflow_id)
        self.workflow.update.assert_called_once_with(self.workflow_data)

    @patch('models.workflow_model.Workflow.get_by_id')
    def test_delete_workflow(self, mock_get_by_id):
        mock_get_by_id.return_value = self.workflow
        result = WorkflowManager.delete_workflow({"id": self.workflow_id})
        self.assertTrue(result)
        mock_get_by_id.assert_called_once_with(self.workflow_id)
        self.workflow.delete.assert_called_once()

    @patch('models.workflow_model.Workflow.get_by_path')
    def test_get_by_path(self, mock_get_by_path):
        mock_get_by_path.return_value = self.workflow
        result = WorkflowManager.get_by_path({"bucketName": "BucketA", "folderPath": "FolderA"})
        self.assertEqual(result, self.workflow.to_dict())
        mock_get_by_path.assert_called_once_with({"bucketName": "BucketA", "folderPath": "FolderA"})

if __name__ == '__main__':
    unittest.main()
