from services.rds_service import RDSService
from helpers.common import get_tenant_id
from aws_lambda_powertools import Logger
from enum import Enum

logger = Logger()

# Define an Enum for the 'action'
class WorkflowAction(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class Workflow:
    def __init__(self, id=None, triggerName=None, projectName=None, bucketName=None, folderPath=None, action=None, workflowId=None):
        self.id = id
        self.tenant_id = get_tenant_id()
        self.trigger_name = triggerName
        self.project_name = projectName
        self.workflow_id = workflowId
        self.bucket_name = bucketName
        self.folder_path = folderPath
        self.action = WorkflowAction(action) if isinstance(action, str) else action
    
    def to_dict(self):
        """
        Convert the Workflow object to a dictionary.
        """
        return {
            'id': self.id,
            'triggerName': self.trigger_name,
            'projectName': self.project_name,
            'workflowId': self.workflow_id,
            'bucketName': self.bucket_name,
            'folderPath': self.folder_path,
            'action': self.action.value
        }

    @classmethod
    def get_all(cls):
        """
        Retrieve all workflows from the Workflow table.
        
        Returns:
            list: List of workflow objects.
        """
        try:
            select_query = "SELECT * FROM Workflow ORDER BY createdAt desc;"
            results = RDSService.execute_query(select_query)
            
            workflows = [
                cls(
                    id=workflow["id"],
                    triggerName=workflow["triggername"],
                    projectName=workflow["projectname"],
                    workflowId=workflow["workflowid"],
                    bucketName=workflow["bucketname"],
                    folderPath=workflow["folderpath"],
                    action=WorkflowAction(workflow["action"])  # Convert string to enum
                ) for workflow in results
            ]

            return workflows
        except Exception as e:
            logger.error(f"Error retrieving workflows: {str(e)}")
            raise e

    def save(self):
        """
        Save the current Workflow object to the database.
        
        Returns:
            None
        """
        try:
            insert_query = (
                "INSERT INTO Workflow (triggerName, projectName, workflowId, bucketName, folderPath, action) "
                "VALUES (%s, %s, %s, %s, %s, %s);"
            )
            params = (
                self.trigger_name,
                self.project_name,
                self.workflow_id,
                self.bucket_name,
                self.folder_path,
                self.action.value  # Store the enum as its string value
            )
            RDSService.execute_query(insert_query, params)
        except Exception as e:
            logger.error(f"Error saving workflow: {str(e)}")
            raise e

    def delete(self):
        """
        Delete the current Document object from the database.

        Returns:
            None
        """
        try:
            delete_query = "DELETE FROM Workflow WHERE id = %s;"
            RDSService.execute_query(delete_query, (self.id,))
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise e
        
    def update(self, workflow_data):
        """
        Update the current Workflow object in the database.

        Args:
            workflow_data (dict): Dictionary containing the updated workflow data.

        Returns:
            None
        """
        try:
            update_query = (
                "UPDATE Workflow SET triggerName = %s, projectName = %s, workflowId = %s, bucketName = %s, folderPath = %s, action = %s "
                "WHERE id = %s;"
            )
            params = (
                workflow_data.get("triggerName", self.trigger_name),
                workflow_data.get("projectName", self.project_name),
                workflow_data.get("workflowId", self.workflow_id),
                workflow_data.get("bucketName", self.bucket_name),
                workflow_data.get("folderPath", self.folder_path),
                workflow_data.get("action", self.action),
                self.id
            )
            RDSService.execute_query(update_query, params)
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise e

    @classmethod
    def get_by_id(cls, _id):
        """
        Retrieve a specific Workflow by its ID.

        Args:
            _id (int): The ID of the Workflow.

        Returns:
            Workflow: The Workflow object if found, else None.
        """
        try:
            select_query = "SELECT * FROM Workflow WHERE id = %s;"
            result = RDSService.execute_query(select_query, (_id,))
            
            if result:
                workflow = result[0]
                return cls(
                    id=workflow["id"],
                    triggerName=workflow["triggername"],
                    projectName=workflow["projectname"],
                    workflowId=workflow["workflowid"],
                    bucketName=workflow["bucketname"],
                    folderPath=workflow["folderpath"],
                    action=WorkflowAction(workflow["action"])  # Convert string to enum
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving Workflow by ID: {str(e)}")
            raise e
    
    @classmethod
    def get_by_path(cls, data):
        """
        Retrieve a specific Workflow by path.

        Args:
            data(Dict) : contain the path info

        Returns:
            Workflow: The Workflow object if found, else None.
        """
        try:
            select_query = "SELECT * FROM Workflow WHERE bucketName = %s AND folderPath = %s;"
            params = (
                data.get("bucketName"),
                data.get("folderPath")
            )
            result = RDSService.execute_query(select_query, params)
            
            if result:
                workflow = result[0]
                return cls(
                    id=workflow["id"],
                    triggerName=workflow["triggername"],
                    projectName=workflow["projectname"],
                    workflowId=workflow["workflowid"],
                    bucketName=workflow["bucketname"],
                    folderPath=workflow["folderpath"],
                    action=WorkflowAction(workflow["action"])  # Convert string to enum
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving Workflow by ID: {str(e)}")
            raise e