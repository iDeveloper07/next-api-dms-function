import unittest
from unittest.mock import patch, MagicMock
import json

from aws_lambda_powertools import Logger
from app import app

# Ensure aws_lambda_powertools Logger is handled properly
with patch('aws_lambda_powertools.Logger', autospec=True):
    from src.handlers.workflow import get_workflows, save_workflow, update_workflow, delete_workflow, get_workflow_status

class TestWorkflowHandler(unittest.TestCase):
    def setUp(self):
        self.mock_logger = Logger()
        app.current_event = MagicMock()
        self.workflow_data = {
            "triggerName": "Trigger1",
            "projectName": "Project1",
            "workflowId": "W1",
            "bucketName": "Bucket1",
            "action": "CREATE"
        }
        self.workflow_status_data = {
            "bucketName": "Bucket1"
        }
        self.workflow_id_data = {
            "id": 1
        }
        self.workflow_list = [self.workflow_data]

    @patch("managers.workflow_manager.WorkflowManager.get_all_workflows")
    def test_get_workflows(self, mock_get_all_workflows):
        mock_get_all_workflows.return_value = self.workflow_list

        response = get_workflows()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.workflow_list)

    @patch("managers.workflow_manager.WorkflowManager.save_workflow")
    def test_save_workflow(self, mock_save_workflow):
        app.current_event.json_body = self.workflow_data
        mock_save_workflow.return_value = None

        response = save_workflow()

        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(json.loads(response['body']), {'message': 'The workflow trigger saved successfully'})

    @patch("managers.workflow_manager.WorkflowManager.update_workflow")
    def test_update_workflow(self, mock_update_workflow):
        app.current_event.json_body = self.workflow_data
        mock_update_workflow.return_value = None

        response = update_workflow()

        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(json.loads(response['body']), {'message': 'The workflow trigger updated successfully'})

    @patch("managers.workflow_manager.WorkflowManager.delete_workflow", return_value=True)
    def test_delete_workflow(self, mock_delete_workflow):
        app.current_event.json_body = self.workflow_id_data

        response = delete_workflow()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'message': 'The workflow trigger deleted successfully'})

    @patch("managers.workflow_manager.WorkflowManager.get_by_path")
    def test_get_workflow_status(self, mock_get_by_path):
        app.current_event.json_body = self.workflow_status_data
        mock_get_by_path.return_value = self.workflow_data

        response = get_workflow_status()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.workflow_data)

if __name__ == "__main__":
    unittest.main()
