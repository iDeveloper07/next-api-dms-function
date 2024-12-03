import unittest
from unittest.mock import patch
from src.models.workflow_model import Workflow, WorkflowAction

class TestWorkflow(unittest.TestCase):
    def setUp(self):
        # Setup a sample workflow data for testing
        self.workflow_data = {
            "id": 1,
            "triggerName": "Data Processing",
            "projectName": "Data Analytics",
            "bucketName": "data-storage",
            "folderPath": "2023/datasets",
            "action": "CREATE",
            "workflowId": "wf-12345"
        }

    @patch('services.rds_service.RDSService.execute_query')
    def test_get_all(self, mock_execute_query):
        # Mocking the database response
        mock_execute_query.return_value = [{
            "id": 1,
            "triggername": "Data Processing",
            "projectname": "Data Analytics",
            "bucketname": "data-storage",
            "folderpath": "2023/datasets",
            "action": "CREATE",
            "workflowid": "wf-12345"
        }]
        
        # Method under test
        workflows = Workflow.get_all()

        # Assertions
        self.assertEqual(len(workflows), 1)
        self.assertIsInstance(workflows[0], Workflow)
        self.assertEqual(workflows[0].trigger_name, "Data Processing")

    @patch('services.rds_service.RDSService.execute_query')
    def test_save(self, mock_execute_query):
        # Create a workflow instance using correct parameter passing
        workflow = Workflow(
            id=1,
            triggerName="Data Processing",
            projectName="Data Analytics",
            bucketName="data-storage",
            folderPath="2023/datasets",
            action="CREATE",
            workflowId="wf-12345"
        )

        # Method under test
        workflow.save()

        # Assertions to ensure SQL is being called correctly
        mock_execute_query.assert_called_once()
        called_args = mock_execute_query.call_args[0]
        self.assertIn("INSERT INTO Workflow", called_args[0])
        self.assertEqual(called_args[1], ("Data Processing", "Data Analytics", "wf-12345", "data-storage", "2023/datasets", "CREATE"))

    @patch('services.rds_service.RDSService.execute_query')
    def test_update(self, mock_execute_query):
        # Create a workflow instance using correct parameter passing
        workflow = Workflow(
            id=1,
            triggerName="Data Processing",
            projectName="Data Analytics",
            bucketName="data-storage",
            folderPath="2023/datasets",
            action="CREATE",
            workflowId="wf-12345"
        )
        new_data = {
            "triggerName": "Updated Data Processing",
            "projectName": "Updated Data Analytics"
        }

        # Method under test
        workflow.update(new_data)

        # Assertions
        mock_execute_query.assert_called_once()
        called_args = mock_execute_query.call_args[0]
        self.assertIn("UPDATE Workflow SET", called_args[0])
        self.assertIn("Updated Data Processing", called_args[1])

    @patch('services.rds_service.RDSService.execute_query')
    def test_delete(self, mock_execute_query):
        # Create a workflow instance using correct parameter passing
        workflow = Workflow(
            id=1,
            triggerName="Data Processing",
            projectName="Data Analytics",
            bucketName="data-storage",
            folderPath="2023/datasets",
            action="CREATE",
            workflowId="wf-12345"
        )

        # Method under test
        workflow.delete()

        # Assertions
        mock_execute_query.assert_called_once_with("DELETE FROM Workflow WHERE id = %s;", (1,))

if __name__ == '__main__':
    unittest.main()
