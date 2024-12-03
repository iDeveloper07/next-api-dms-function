import json
from app import app
from managers.workflow_manager import WorkflowManager
from aws_lambda_powertools import Logger

logger = Logger()

@app.get("/workflows")
def get_workflows():
    """
    Retrieve all workflows from the Workflow table.
    
    Returns:
        dict: JSON response containing the list of workflows or an error message.
    """
    try:
        results = WorkflowManager.get_all_workflows()
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str)
        }
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


@app.put("/workflows")
def save_workflow():
    """
    Save a new workflow to the Workflow table.
    
    Returns:
        dict: JSON response indicating success or failure of the operation.
    """
    try:
        data = app.current_event.json_body
        
        # Validate required fields
        if not all([data.get("triggerName"), data.get("projectName"), data.get("workflowId"), data.get("bucketName"), data.get("action")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        WorkflowManager.save_workflow(data)

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'The workflow trigger saved successfully'})
        }
    except Exception as e:
        logger.error(f"Failed to save workflow: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
    

@app.post("/workflows")
def update_workflow():
    """
    Update the exsiting workflow to the Workflow table.
    
    Returns:
        dict: JSON response indicating success or failure of the operation.
    """
    try:
        data = app.current_event.json_body
        
        # Validate required fields
        if not all([data.get("triggerName"), data.get("projectName"), data.get("workflowId"), data.get("bucketName"), data.get("action")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        WorkflowManager.update_workflow(data)

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'The workflow trigger updated successfully'})
        }
    except Exception as e:
        logger.error(f"Failed to save workflow: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
    

@app.delete("/workflows")
def delete_workflow():
    """

    Delete the exsiting workflow to the Workflow table.
    
    Returns:
        dict: JSON response indicating success or failure of the operation.
    """
    try:
        data = app.current_event.json_body
        
        # Validate required fields
        if not all([data.get("id")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        deleted = WorkflowManager.delete_workflow(data)

        if deleted:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'The workflow trigger deleted successfully'})
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Workflow not found'})
            }
    
    except Exception as e:
        logger.error(f"Failed to save workflow: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
    

@app.post("/workflows/status")
def get_workflow_status():
    """
    Get the exsiting workflow to the Workflow table.
    
    Returns:
        dict: JSON response indicating the workflow
    """
    try:
        data = app.current_event.json_body
        
        # Validate required fields
        if not all([data.get("bucketName")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        result = WorkflowManager.get_by_path(data)

        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)
        }
    except Exception as e:
        logger.error(f"Failed to get workflow by path: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }