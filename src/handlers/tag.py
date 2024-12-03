import json
from app import app
from managers.tag_manager import TagManager
from aws_lambda_powertools import Logger

logger = Logger()


@app.post("/tags")
def create_tag():
    """
    Create a new tag in the Tags table.

    Returns:
        dict: JSON response indicating success or failure of the operation.
    """
    try:
        data = app.current_event.json_body

        # Validate required fields
        if not all([data.get("tagKey"), data.get("tagValue")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        if TagManager.check_tag_exists(data.get("tagKey")):
            return {
                'statusCode': 409,
                'body': json.dumps({'error': 'Tag with the same key already exists'})
            }

        TagManager.save_tag(data)

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Tag created successfully'})
        }
    except Exception as e:
        logger.error(f"Failed to create tag: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

@app.get("/tags")
def get_tags():
    """
    Retrieve all tags from the Tags table.

    Returns:
        dict: JSON response containing the list of tags or an error message.
    """
    try:
        results = TagManager.get_all_tags()
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str)
        }
    except Exception as e:
        logger.error(f"Failed to list tags: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

@app.get("/tags/<tag_key>")
def get_tag(tag_key):
    """
    Retrieve all tags from the Tags table.

    Returns:
        dict: JSON response containing the list of tags or an error message.
    """
    try:
        results = TagManager.get_tag_by_key(tag_key)
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str)
        }
    except Exception as e:
        logger.error(f"Failed to list tags: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
    

@app.delete("/tags/<tag_key>")
def delete_tag(tag_key):
    """
    Delete a tag by its ID from the Tags table if it is not associated with any documents.

    Returns:
        dict: JSON response indicating success or failure of the deletion.
    """
    try:
        deleted = TagManager.delete_tag(tag_key)
        if deleted:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Tag deleted successfully'})
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Tag is associated with one or more documents and cannot be deleted.'})
            }
    except Exception as e:
        logger.error(f"Failed to delete tag: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


@app.post("/tags/document")
def create_document_tag():
    """
    Create a new association between a document and a tag (many-to-many relationship).

    Returns:
        dict: JSON response indicating success or failure of the operation.
    """
    try:
        data = app.current_event.json_body

        # Validate required fields
        if not all([data.get("bucketName"), data.get("documentId"), data.get("tags")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        TagManager.save_document_tag(data)

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Document tag association created successfully'})
        }
    except Exception as e:
        logger.error(f"Failed to create document tag association: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


@app.get("/tags/document/<document_id>")
def get_document_tags(document_id):
    """
    Retrieve all tags for a specific document by its document ID.

    Returns:
        dict: JSON response containing the list of tags for the document or an error message.
    """
    try:
        results = TagManager.get_tags_for_document(document_id)
        if results:
            return {
                'statusCode': 200,
                'body': json.dumps(results, default=str)
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document tags not found'})
            }
    except Exception as e:
        logger.error(f"Failed to retrieve tags for document: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
    

@app.delete("/tags/document")
def delete_document_tag():
    """
    Delete a tag association for a document by its document ID and tag ID.

    Returns:
        dict: JSON response indicating success or failure of the deletion.
    """
    try:
        data = app.current_event.json_body

        # Validate required fields
        if not all([data.get("bucketName"), data.get("documentId"), data.get("tags")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        deleted = TagManager.delete_document_tag(data)
        if deleted:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Document tag association deleted successfully'})
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document tag association not found'})
            }
    except Exception as e:
        logger.error(f"Failed to delete document tag association: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
