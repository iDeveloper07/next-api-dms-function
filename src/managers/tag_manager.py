from aws_lambda_powertools import Logger
from models.tag_model import Tag, DocumentTag
from services.logging_service import log_execution_time

logger = Logger()

class TagManager:

    @staticmethod
    @log_execution_time
    def get_all_tags():
        """
        Retrieve all tags using the Tag model.

        Returns:
            list: List of Tag objects.
        """
        try:
            logger.info("Fetching all tags.")
            tags = Tag.get_all()

            return [tag.to_dict() for tag in tags]
        except Exception as e:
            logger.error(f"Error retrieving tags: {str(e)}")
            raise e
        
    @staticmethod
    @log_execution_time
    def get_tag_by_key(tag_key):
        """
        Retrieve a tag by its key using the Tag model.

        Args:
            tag_key (str): The key of the tag to retrieve.

        Returns:
            Tag: The Tag object if found, else None.
        """
        try:
            logger.info(f"Retrieving tag with key '{tag_key}'.")
            return Tag.get_by_key(tag_key).to_dict()
        except Exception as e:
            logger.error(f"Error retrieving tag by key: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def get_tags_for_document(document_id):
        """
        Retrieve all tags for a specific document by its ID.

        Args:
            document_id (int): The ID of the document to retrieve tags for.

        Returns:
            list: List of tags for the document.
        """
        try:
            logger.info(f"Fetching tags for document ID {document_id}.")
            tags = DocumentTag.get_tags_for_document(document_id)

            return [tag.to_dict() for tag in tags]
        except Exception as e:
            logger.error(f"Error retrieving tags for document: {str(e)}")
            raise e


    @staticmethod
    @log_execution_time
    def save_tag(tag_data):
        """
        Save a new tag using the Tag model.

        Args:
            tag_data (dict): Dictionary containing the tag data.

        Returns:
            None
        """
        try:
            logger.info(f"Saving new tag with key {tag_data.get('tagKey')}.")
            new_tag = Tag(
                tag_key=tag_data.get("tagKey"),
                tag_value=tag_data.get("tagValue")
            )
            new_tag.save()
        except Exception as e:
            logger.error(f"Error saving tag: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def check_tag_exists(tag_key):
        """
        Check if a tag with the same key already exists using the Tag model.

        Args:
            tag_key (str): The key of the tag to check.

        Returns:
            bool: True if the tag exists, False otherwise.
        """
        try:
            logger.info(f"Checking if tag with key '{tag_key}' exists.")
            return Tag.exists_by_key(tag_key)
        except Exception as e:
            logger.error(f"Error checking if tag exists: {str(e)}")
            raise e  

    @staticmethod
    @log_execution_time
    def save_document_tag(association_data):
        """
        Save a new document-tag association (many-to-many) using the DocumentTag model.

        Args:
            association_data (dict): Dictionary containing the document and tag association data.

        Returns:
            None
        """
        try:
            logger.info(f"Saving document-tag association for document {association_data.get('documentId')} and tag {association_data.get('tagKeys')}.")
            bucketName=association_data.get("bucketName")
            documentId=association_data.get("documentId")
            tags=association_data.get("tags")

            for tag in tags:
                new_association = DocumentTag(
                    bucket_name=bucketName,
                    document_id=documentId,
                    tag_key=tag.get("Key")
                )
                new_association.save()
                
        except Exception as e:
            logger.error(f"Error saving document-tag association: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def delete_tag(tag_key):
        """
        Delete a tag by its ID if it is not associated with any documents.

        Args:
            tag_id (int): The ID of the tag to delete.

        Returns:
            bool: True if the tag was deleted, False if it is still associated with documents.
        """
        try:
            logger.info(f"Checking if tag with ID {tag_key} is associated with any documents.")
            
            # Check if the tag is associated with any documents
            is_associated = DocumentTag.is_tag_associated(tag_key)
            if is_associated:
                logger.error(f"Tag {tag_key} is associated with one or more documents. Deletion not allowed.")
                return False
            
            # If not associated, proceed with deletion
            Tag.delete(tag_key)
            return True
        except Exception as e:
            logger.error(f"Error deleting tag: {str(e)}")
            raise e
        
    @staticmethod
    @log_execution_time
    def delete_document_tag(association_data):
        """
        Delete a document-tag association by document ID and tag ID.

        Args:
            document_id (int): The ID of the document.
            tag_id (int): The ID of the tag.

        Returns:
            bool: True if the association was deleted, False if not found.
        """
        try:
            logger.info(f"Deleting document-tag association for document {association_data.get('documentId')} and tag {association_data.get("tags")}.")

            bucketName=association_data.get("bucketName")
            documentId=association_data.get("documentId")
            tags=association_data.get("tags")

            result = False
            for tag in tags:
                association = DocumentTag.get_association(bucketName, documentId, tag.get("Key"))
                if association:
                    association.delete()
                    result |= True
                result |= False
        except Exception as e:
            logger.error(f"Error deleting document-tag association: {str(e)}")
            raise e
