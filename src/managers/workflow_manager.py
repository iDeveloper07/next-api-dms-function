from aws_lambda_powertools import Logger
from models.workflow_model import Workflow
from services.logging_service import log_execution_time

logger = Logger()

class WorkflowManager:
    
    @staticmethod
    @log_execution_time
    def get_all_workflows():
        """
        Retrieve all workflows using the Workflow model.
        
        Returns:
            list: List of Workflow objects.
        """
        try:
            logger.info("Fetching all workflows.")
            workflows = Workflow.get_all()
            
            # Convert each Workflow object to a dictionary using `to_dict()`
            return [workflow.to_dict() for workflow in workflows]
        except Exception as e:
            logger.error(f"Error retrieving workflows: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def save_workflow(workflow_data):
        """
        Save a new workflow using the Workflow model.
        
        Args:
            workflow_data (dict): Dictionary containing the workflow data.
        
        Returns:
            None
        """
        try:
            logger.info(f"Saving new workflow for action {workflow_data.get('action')}.")
            new_workflow = Workflow(
                triggerName=workflow_data.get("triggerName"),
                projectName=workflow_data.get("projectName"),
                workflowId=workflow_data.get("workflowId"),
                bucketName=workflow_data.get("bucketName"),
                folderPath=workflow_data.get("folderPath"),
                action=workflow_data.get("action")
            )
            new_workflow.save()
        except Exception as e:
            logger.error(f"Error saving workflow: {str(e)}")
            raise e
        

    @staticmethod
    @log_execution_time
    def update_workflow(workflow_data):
        """
        Update existing  workflow using the Workflow model.
        
        Args:
            bool: True if the workflow was updated, False if not found.
        
        Returns:
            None
        """
        try:
            logger.info(f"Updating workflow with ID  {workflow_data.get('id')}.")
            id = workflow_data.get('id')
            workflow = Workflow.get_by_id(id)
            if workflow:
                workflow.update(workflow_data)
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving workflow: {str(e)}")
            raise e
        
    @staticmethod
    @log_execution_time
    def delete_workflow(workflow_data):
        """
        Delete a workflow by id.
        
        Args:
            workflow_data(Dict) : contain the workflow info
        
        Returns:
            bool: True if the workflow was deleted, False if not found.
        """
        try:
            logger.info(f"Deleting workflow with ID  {workflow_data.get('id')}.")
            id = workflow_data.get('id')
            workflow = Workflow.get_by_id(id)
            if workflow:
                workflow.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving workflow: {str(e)}")
            raise e
    
    @staticmethod
    @log_execution_time
    def get_by_path(data):
        """
        Get a workflow by path.
        
        Args:
            data(Dict) : contain the path info
        
        Returns:
            Dict: JSON response containing the list of workflows
        """
        try:
            logger.info(f"Getting workflow with apth  {data.get('bucketName')}/{data.get('folderPath')}.")
            result = Workflow.get_by_path(data)
            if result:
                return result.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting workflow: {str(e)}")
            raise e