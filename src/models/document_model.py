from services.rds_service import RDSService
from helpers.common import get_tenant_id
from aws_lambda_powertools import Logger

logger = Logger()

class Document:
    def __init__(self, id=None, bucket_name=None, name=None, key=None, prefix=None, size=None, type=None, hash=None, version=None, created_at=None):
        self.id = id
        self.tenant_id = get_tenant_id()
        self.bucket_name = bucket_name
        self.name = name
        self.key = key
        self.prefix = prefix
        self.size = size
        self.type = type
        self.hash = hash
        self.version = version
        self.created_at = created_at

    def to_dict(self):
        """
        Convert the Document object to a dictionary for JSON serialization.
        """
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'bucket_name': self.bucket_name,
            'name': self.name,
            'key': self.key,
            'prefix': self.prefix,
            'size': self.size,
            'type': self.type,
            'hash': self.hash,
            'version': self.version,
            'created_at': self.created_at
        }

    @classmethod
    def get_all(cls):
        """
        Retrieve all documents from the Documents table.

        Returns:
            list: List of document objects.
        """
        try:
            select_query = "SELECT * FROM Documents;"
            results = RDSService.execute_query(select_query)
            
            documents = [
                cls(
                    id=document["id"],
                    bucket_name=document["bucketname"],
                    name=document["name"],
                    key=document["key"],
                    prefix=document["prefix"],
                    size=document["size"],
                    type=document["type"],
                    hash=document["hash"],
                    version=document["version"],
                    created_at=document["createdat"]
                ) for document in results
            ]
            
            return documents
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            raise e

    @classmethod
    def get_by_id(cls, document_id):
        """
        Retrieve a specific document by its ID.

        Args:
            document_id (int): The ID of the document.

        Returns:
            Document: The Document object if found, else None.
        """
        try:
            select_query = "SELECT * FROM Documents WHERE id = %s;"
            result = RDSService.execute_query(select_query, (document_id,))
            
            if result:
                document = result[0]
                return cls(
                    id=document["id"],
                    bucket_name=document["bucketname"],
                    name=document["name"],
                    key=document["key"],
                    prefix=document["prefix"],
                    size=document["size"],
                    type=document["type"],
                    hash=document["hash"],
                    version=document["version"],
                    created_at=document["createdat"]
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving document by ID: {str(e)}")
            raise e
        
    
    @classmethod
    def get_by_key(cls, document_info):
        """
        Retrieve a specific document by its s3.

        Args:
            document_id (int): The ID of the document.

        Returns:
            Document: The Document object if found, else None.
        """
        try:
            bucket_name = document_info.get("bucketName")
            key = document_info.get("key")
            version = document_info.get("version")

            select_query = "SELECT * FROM Documents WHERE bucketName = %s AND key = %s AND version = %s ;"
            result = RDSService.execute_query(select_query, (bucket_name, key, version,))
            
            if result:
                document = result[0]
                return cls(
                    id=document["id"],
                    bucket_name=document["bucketname"],
                    name=document["name"],
                    key=document["key"],
                    prefix=document["prefix"],
                    size=document["size"],
                    type=document["type"],
                    hash=document["hash"],
                    version=document["version"],
                    created_at=document["createdat"]
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving document by ID: {str(e)}")
            raise e
       

    @classmethod
    def get_documents_by_tag(cls, tag_key):
        """
        Retrieve all documents associated with a specific tag by its tag ID.

        Args:
            tag_id (int): The ID of the tag.

        Returns:
            list: List of Document objects associated with the tag.
        """
        try:
            select_query = """
                SELECT d.* FROM DocumentTags dt
                JOIN Documents d ON dt.documentId = d.id
                WHERE dt.tagKey = %s;
            """
            results = RDSService.execute_query(select_query, (tag_key,))

            documents = [
                Document(
                    id=document["id"],
                    bucket_name=document["bucketname"],
                    name=document["name"],
                    key=document["key"],
                    prefix=document["prefix"],
                    size=document["size"],
                    type=document["type"],
                    hash=document["hash"],
                    version=document["version"],
                    created_at=document.get("createdat")  # Assuming created_at exists in Documents table
                ) for document in results
            ]

            return documents  # Return a list of Document objects
        except Exception as e:
            logger.error(f"Error retrieving documents for tag: {str(e)}")
            raise e

    @classmethod
    def get_by_type(cls, data):
        """
        Retrieve a specific document by its s3.

        Args:
            document_id (int): The ID of the document.

        Returns:
            Document: The Document object if found, else None.
        """
        try:
            bucket_name = data.get("bucketName")
            type = data.get("type")
            key = data.get("key")
            version = data.get("version")

            if type == "bucket" :
                select_query = "SELECT * FROM Documents WHERE bucketName = %s;"
                result = RDSService.execute_query(select_query, (bucket_name,))
            elif type == "folder" :
                select_query = "SELECT * FROM Documents WHERE bucketName = %s AND prefix = %s;"
                result = RDSService.execute_query(select_query, (bucket_name, key,))
            elif type == "document" :
                select_query = "SELECT * FROM Documents WHERE bucketName = %s AND key = %s AND version = %s ;"
                result = RDSService.execute_query(select_query, (bucket_name, key, version, ))

            if result:
                documents = [
                    Document(
                        id=document["id"],
                        bucket_name=document["bucketname"],
                        name=document["name"],
                        key=document["key"],
                        prefix=document["prefix"],
                        size=document["size"],
                        type=document["type"],
                        hash=document["hash"],
                        version=document["version"],
                        created_at=document.get("createdat")  # Assuming created_at exists in Documents table
                    ) for document in result
                ]
                return documents
            return None
        except Exception as e:
            logger.error(f"Error retrieving document by ID: {str(e)}")
            raise e
       


    def save(self):
        """
        Save the current Document object to the database.

        Returns:
            None
        """
        try:
            insert_query = (
                "INSERT INTO Documents (bucketName, name, key, prefix, size, type, hash, version) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
            )
            params = (
                self.bucket_name,
                self.name,
                self.key,
                self.prefix,
                self.size,
                self.type,
                self.hash,
                self.version
            )
            RDSService.execute_query(insert_query, params)
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            raise e

    def update(self, document_data):
        """
        Update the current Document object in the database.

        Args:
            document_data (dict): Dictionary containing the updated document data.

        Returns:
            None
        """
        try:
            update_query = (
                "UPDATE Documents SET bucketName = %s, name = %s, key = %s, prefix = %s, size = %s, type = %s, hash = %s, version = %s "
                "WHERE id = %s;"
            )
            params = (
                document_data.get("bucketName", self.bucket_name),
                document_data.get("name", self.name),
                document_data.get("key", self.key),
                document_data.get("prefix", self.prefix),
                document_data.get("size", self.size),
                document_data.get("type", self.type),
                document_data.get("hash", self.hash),
                document_data.get("version", self.version),
                self.id
            )
            RDSService.execute_query(update_query, params)
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise e

    def delete(self):
        """
        Delete the current Document object from the database.

        Returns:
            None
        """
        try:
            delete_query = "DELETE FROM Documents WHERE id = %s;"
            RDSService.execute_query(delete_query, (self.id,))
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise e
        
    @classmethod
    def get_documents_by_name_tag(cls, data):
        """
        Retrieve all documents associated with specific tags or name.

        Args:
            document_data (dict): Dictionary containing the document data.

        Returns:
            list: List of Document objects.
        """
        try:
            bucketName = data.get("bucketName")
            name = data.get("name")
            tag_keys = data.get("tag_keys")

            # Start building the query
            query_parts = ["SELECT DISTINCT d.* FROM Documents d"]
            joins = []
            conditions = ["d.bucketName = %s"]  # Since bucketName is always provided

            # Add conditions for name if provided, using LIKE for partial matches
            if name:
                conditions.append("d.name ILIKE %s")
                name = f"%{name}%"  # Prepare the name for a LIKE query

            # Handle tag_keys if provided and not empty
            if tag_keys:
                joins.append("JOIN DocumentTags dt ON dt.documentId = d.id")
                tag_conditions = " OR ".join(["dt.tagKey = %s" for _ in tag_keys])
                conditions.append(f"({tag_conditions})")

            # Combine the parts of the query
            if joins:
                query_parts.extend(joins)
            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))

            select_query = " ".join(query_parts) + ";"

            # Prepare the parameters for the query based on the conditions used
            params = [bucketName]
            if name:
                params.append(name)  # Add modified name with wildcards
            params.extend(tag_keys)

            # Execute the query with the collected parameters
            results = RDSService.execute_query(select_query, tuple(params))


            documents = [
                Document(
                    id=document["id"],
                    bucket_name=document["bucketname"],
                    name=document["name"],
                    key=document["key"],
                    prefix=document["prefix"],
                    size=document["size"],
                    type=document["type"],
                    hash=document["hash"],
                    version=document["version"],
                    created_at=document.get("createdat")  # Assuming created_at exists in Documents table
                ) for document in results
            ]

            return documents  # Return a list of Document objects
        except Exception as e:
            logger.error(f"Error retrieving documents for tag: {str(e)}")
            raise e

