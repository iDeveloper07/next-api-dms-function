from services.rds_service import RDSService
from helpers.common import get_tenant_id
from aws_lambda_powertools import Logger
from models.document_model import Document

logger = Logger()

class Tag:
    def __init__(self, id=None, tag_key=None, tag_value=None):
        self.id = id
        self.tenant_id = get_tenant_id()
        self.tag_key = tag_key
        self.tag_value = tag_value

    def to_dict(self):
        """
        Convert the Tag object to a dictionary for JSON serialization.
        """
        return {
            'id': self.id,
            'tag_key': self.tag_key,
            'tag_value': self.tag_value,
        }
    
    @classmethod
    def get_by_id(cls, tag_id):
        """
        Retrieve a specific tag by its ID.

        Args:
            tag_id (int): The ID of the tag.

        Returns:
            Tag: The Tag object if found, else None.
        """
        try:
            select_query = "SELECT * FROM Tags WHERE id = %s;"
            result = RDSService.execute_query(select_query, (tag_id,))
            if result:
                tag = result[0]
                return cls(
                    id=tag["id"],
                    tag_key=tag["tagkey"],
                    tag_value=tag["tagvalue"],
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving tag by ID: {str(e)}")
            raise e


    @classmethod
    def get_by_key(cls, tag_key):
        """
        Retrieve a tag by its key for the current tenant.

        Args:
            tag_key (str): The key of the tag to retrieve.

        Returns:
            Tag: The Tag object if found, else None.
        """
        try:
            select_query = "SELECT * FROM Tags WHERE tagKey = %s;"
            result = RDSService.execute_query(select_query, (tag_key,))
            
            if result:
                tag = result[0]
                return cls(
                    id=tag["id"],
                    tag_key=tag["tagkey"],
                    tag_value=tag["tagvalue"],
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving tag by key: {str(e)}")
            raise e
        

    @classmethod
    def get_all(cls):
        """
        Retrieve all tags from the Tags table.

        Returns:
            list: List of Tag objects.
        """
        try:
            select_query = "SELECT * FROM Tags;"
            results = RDSService.execute_query(select_query)
            tags = [
                cls(
                    id=tag["id"],
                    tag_key=tag["tagkey"],
                    tag_value=tag["tagvalue"],
                ) for tag in results
            ]

            return tags
        except Exception as e:
            logger.error(f"Error retrieving tags: {str(e)}")
            raise e
    
    @classmethod
    def exists_by_key(cls, tag_key):
        """
        Check if a tag with the same key already exists.

        Args:
            tag_key (str): The tag key to check for.

        Returns:
            bool: True if a tag with the same key exists, False otherwise.
        """
        try:
            select_query = "SELECT COUNT(*) FROM Tags WHERE tagKey = %s;"
            result = RDSService.execute_query(select_query, (tag_key,))
            return result[0]['count'] > 0
        except Exception as e:
            logger.error(f"Error checking if tag exists by key: {str(e)}")
            raise e

    def save(self):
        """
        Save the current Tag object to the database.

        Returns:
            None
        """
        try:
            insert_query = (
                "INSERT INTO Tags (tagKey, tagValue) "
                "VALUES ( %s, %s);"
            )
            params = (
                self.tag_key,
                self.tag_value
            )

            RDSService.execute_query(insert_query, params)
        except Exception as e:
            logger.error(f"Error saving tag: {str(e)}")
            raise e
    
    @classmethod
    def delete(cls, tag_key):
        """
        Delete the current Tag object from the database.

        Returns:
            None
        """
        try:
            delete_query = "DELETE FROM Tags WHERE tagkey = %s;"
            RDSService.execute_query(delete_query, (tag_key,))
        except Exception as e:
            logger.error(f"Error deleting tag: {str(e)}")
            raise e


class DocumentTag:
    def __init__(self, id=None, bucket_name = None, document_id=None, tag_key=None):
        self.tenant_id = get_tenant_id()
        self.id = id
        self.bucket_name = bucket_name
        self.document_id = document_id
        self.tag_key = tag_key

    def to_dict(self):
        """
        Convert the DocumentTag object to a dictionary for JSON serialization.
        """
        return {
            'id': self.id,
            'bucket_name': self.bucket_name,
            'document_id': self.document_id,
            'tag_key': self.tag_key,
        }


    @classmethod
    def get_tags_for_document(cls, document_id):
        """
        Retrieve all tags for a specific document by its ID.

        Returns:
            list: List of tag objects associated with the document.
        """
        try:
            select_query = """
                SELECT t.* FROM DocumentTags dt
                JOIN Tags t ON dt.tagKey = t.tagKey
                WHERE dt.documentId = %s;
            """
            results = RDSService.execute_query(select_query, (document_id,))
            
            tags = [
                Tag(
                    id=tag["id"],
                    tag_key=tag["tagkey"],
                    tag_value=tag["tagvalue"],
                ) for tag in results
            ]

            return tags
        except Exception as e:
            logger.error(f"Error retrieving tags for document: {str(e)}")
            raise e

    @classmethod
    def get_association(cls, bucketName, document_id, tag_key):
        """
        Retrieve a specific document-tag association by document ID and tag ID.

        Args:
            document_id (int): The ID of the document.
            tag_id (int): The ID of the tag.

        Returns:
            DocumentTag: The DocumentTag object if found, else None.
        """
        try:
            select_query = "SELECT * FROM DocumentTags WHERE bucketName = %s AND documentId = %s AND tagKey = %s;"
            result = RDSService.execute_query(select_query, (bucketName, document_id, tag_key))
            if result:
                documentTag = result[0]
                return cls(
                    id=documentTag["id"],
                    tag_key=documentTag["tagkey"],
                    document_id=documentTag["documentid"],
                    bucket_name=documentTag["bucketname"],
                )
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving document-tag association: {str(e)}")
            raise e

    def save(self):
        """
        Save the current DocumentTag association to the database.

        Returns:
            None
        """
        try:
            insert_query = (
                "INSERT INTO DocumentTags (bucketName, documentId, tagKey) "
                "VALUES ( %s, %s, %s);"
            )
            params = (
                self.bucket_name,
                self.document_id,
                self.tag_key
            )
            RDSService.execute_query(insert_query, params)
        except Exception as e:
            logger.error(f"Error saving document-tag association: {str(e)}")
            raise e

    def delete(self):
        """
        Delete the current DocumentTag association from the database.

        Returns:
            None
        """
        try:
            delete_query = "DELETE FROM DocumentTags WHERE bucketName =%s AND documentId = %s AND tagKey = %s;"

            RDSService.execute_query(delete_query, (self.bucket_name, self.document_id, self.tag_key))
        except Exception as e:
            logger.error(f"Error deleting document-tag association: {str(e)}")
            raise e
        
    @staticmethod
    def is_tag_associated(tag_key):
        """
        Check if a tag is associated with any documents.

        Args:
            tag_id (int): The ID of the tag to check.

        Returns:
            bool: True if the tag is associated with any documents, False otherwise.
        """
        try:
            select_query = "SELECT COUNT(*) FROM DocumentTags WHERE tagkey = %s;"
            result = RDSService.execute_query(select_query, (tag_key,))
            return result[0]['count'] > 0
        except Exception as e:
            logger.error(f"Error checking if tag is associated with documents: {str(e)}")
            raise e
