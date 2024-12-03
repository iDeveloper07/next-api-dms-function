from aws_lambda_powertools import Logger
from models.document_model import Document
from services.logging_service import log_execution_time

logger = Logger()

class DocumentManager:

    @staticmethod
    @log_execution_time
    def get_all_documents():
        """
        Retrieve all documents using the Document model.

        Returns:
            list: List of Document objects.
        """
        try:
            logger.info("Fetching all documents.")
            documents =  Document.get_all()
            
            return[document.to_dict() for document in documents]
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def get_document(document_id):
        """
        Retrieve a document by its ID.

        Args:
            document_id (int): The ID of the document to retrieve.

        Returns:
            Document: The Document object if found, else None.
        """
        try:
            logger.info(f"Fetching document with ID {document_id}.")
            return Document.get_by_id(document_id).to_dict()
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            raise e
            

    @staticmethod
    @log_execution_time
    def get_documents_by_tag(tag_key):
        """
        Retrieve all documents associated with a specific tag by its tag ID.

        Args:
            tag_id (int): The ID of the tag.

        Returns:
            list: List of documents associated with the tag.
        """
        try:
            logger.info(f"Fetching documents associated with tag ID {tag_key}.")
            documents = Document.get_documents_by_tag(tag_key)
            
            return[document.to_dict() for document in documents]
        except Exception as e:
            logger.error(f"Error retrieving documents for tag: {str(e)}")
            raise e
            
    @staticmethod
    @log_execution_time
    def save_document(document_data):
        """
        Save a new document using the Document model.

        Args:
            document_data (dict): Dictionary containing the document data.

        Returns:
            None
        """
        try:
            logger.info(f"Saving new document with key {document_data.get('key')}.")
            new_document = Document(
                bucket_name=document_data.get("bucketName"),
                name=document_data.get("name"),
                key=document_data.get("key"),
                prefix=document_data.get("prefix"),
                size=document_data.get("size"),
                type=document_data.get("type"),
                hash=document_data.get("hash"),
                version=document_data.get("version")
            )
            new_document.save()
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def update_document(document_id, document_data):
        """
        Update an existing document.

        Args:
            document_id (int): The ID of the document to update.
            document_data (dict): The updated document data.

        Returns:
            bool: True if the document was updated, False if not found.
        """
        try:
            logger.info(f"Updating document with ID {document_id}.")
            document = Document.get_by_id(document_id)
            if document:
                document.update(document_data)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def delete_document(document_id):
        """
        Delete a document by its ID.

        Args:
            document_id (int): The ID of the document to delete.

        Returns:
            bool: True if the document was deleted, False if not found.
        """
        try:
            logger.info(f"Deleting document with ID {document_id}.")
            document = Document.get_by_id(document_id)
            if document:
                document.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise e
        
    @staticmethod
    @log_execution_time
    def delete_documents(data):
        """
        Delete a document by type.

        Args:
            document_id (int): The ID of the document to delete.

        Returns:
            bool: True if the document was deleted, False if not found.
        """
        try:
            logger.info(f"Deleting documents by type {data}.")
            documents = Document.get_by_type(data)

            result = False
            for document in documents:
                if document:
                    document.delete()
                    result |= True
                result |= False
                
            return result

        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise e
        
    @staticmethod
    @log_execution_time
    def search_documents(data):
        """
        Retrieve the result of documents searched by its name and tag key

        Args:
            document_data (dict): Dictionary containing the document data.

        Returns:
            dict: JSON response containing the list of documents for the tag/document name or an error message.
        """
        try:
            logger.info("Searching documents by name and tag keys.")
            documents = Document.get_documents_by_name_tag(data)
            return[document.to_dict() for document in documents]
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def get_document_by_key(document_info):
        """
        Retrieve a document by its ID.

        Args:
            document_id (int): The ID of the document to retrieve.

        Returns:
            Document: The Document object if found, else None.
        """
        try:
            logger.info(f"Fetching document with s3 key {document_info.get("key")}.")
            return Document.get_by_key(document_info).to_dict()
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            raise e