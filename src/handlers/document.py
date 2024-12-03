import json
from app import app
from managers.document_manager import DocumentManager
from aws_lambda_powertools import Logger

logger = Logger()

@app.get("/documents")
def get_documents():
    """
    Retrieve all documents from the Documents table.

    Returns:
        dict: JSON response containing the list of documents or an error message.
    """
    try:
        results = DocumentManager.get_all_documents()
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str)
        }
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


@app.get("/documents/<document_id>")
def get_document(document_id):
    """
    Retrieve a specific document by its ID.

    Returns:
        dict: JSON response containing the document or an error message.
    """
    try:
        result = DocumentManager.get_document(document_id)
        if result:
            return {
                'statusCode': 200,
                'body': json.dumps(result, default=str)
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document not found'})
            }
    except Exception as e:
        logger.error(f"Failed to retrieve document: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

@app.get("/documents/tag/<tag_key>")
def get_documents_by_tag(tag_key):
    """
    Retrieve all documents associated with a specific tag by its tag ID.

    Returns:
        dict: JSON response containing the list of documents for the tag or an error message.
    """
    try:
        results = DocumentManager.get_documents_by_tag(tag_key)
        if results:
            return {
                'statusCode': 200,
                'body': json.dumps(results, default=str)
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Documents not found for the tag: '})
            }
    except Exception as e:
        logger.error(f"Failed to retrieve documents for tag: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


@app.post("/documents")
def create_document():
    """
    Create a new document in the Documents table.

    Returns:
        dict: JSON response indicating success or failure of the operation.
    """
    try:
        data = app.current_event.json_body

        # Validate required fields
        if not all([data.get("bucketName"), data.get("name"), data.get("key"), data.get("size"), data.get("hash"), data.get("version")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        DocumentManager.save_document(data)

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Document created successfully'})
        }
    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


@app.put("/documents/<document_id>")
def update_document(document_id):
    """
    Update an existing document by its ID.

    Returns:
        dict: JSON response indicating success or failure of the update.
    """
    try:
        data = app.current_event.json_body

        # Update the document
        updated = DocumentManager.update_document(document_id, data)
        if updated:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Document updated successfully'})
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document not found'})
            }
    except Exception as e:
        logger.error(f"Failed to update document: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


@app.delete("/documents/<document_id>")
def delete_document(document_id):
    """
    Delete a document by its ID.

    Returns:
        dict: JSON response indicating success or failure of the deletion.
    """
    try:
        deleted = DocumentManager.delete_document(document_id)
        if deleted:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Document deleted successfully'})
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document not found'})
            }
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

@app.post("/documents/search")
def search_document():
    """
    Retrieve the result of documents searched by its name and tag key

    Returns:
        dict: JSON response containing the search result or an error message.
    """
    try:
        data = app.current_event.json_body

        # Validate required fields
        if not all([data.get("bucketName")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        result = DocumentManager.search_documents(data)
        if result:
            return {
                'statusCode': 200,
                'body': json.dumps(result, default=str)
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document not found'})
            }
    except Exception as e:
        logger.error(f"Failed to retrieve document: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

@app.post("/documents/key")
def get_document_by_key():
    """
    Retrieve a specific document by its S3 key.

    Returns:
        dict: JSON response containing the document or an error message.
    """
    try:
        data = app.current_event.json_body
        # Validate required fields
        if not all([data.get("bucketName"),data.get("key"), data.get("version")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        result = DocumentManager.get_document_by_key(data)

        if result:
            return {
                'statusCode': 200,
                'body': json.dumps(result, default=str)
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document not found'})
            }
    except Exception as e:
        logger.error(f"Failed to retrieve document: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


@app.delete("/documents")
def delete_documents():
    """
    Delete a document/folder/bucket

    Returns:
        dict: JSON response indicating success or failure of the deletion.
    """
    try:
        data = app.current_event.json_body

        # Validate required fields
        if not all([data.get("bucketName"), data.get("type")]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        deleted = DocumentManager.delete_documents(data)
        if deleted:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Document deleted successfully'})
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document not found'})
            }
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

