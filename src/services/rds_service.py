import os
import json
import psycopg2
import boto3
from psycopg2.extras import RealDictCursor
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger
from helpers.common import get_tenant_id
from services.logging_service import log_execution_time


logger = Logger()

class RDSService:
    """
    RDSService provides methods to interact with an RDS instance using an RDS Proxy.
    It includes functionality for creating a database connection, retrieving credentials,
    and executing SQL queries with tenant-specific context.
    """

    _connection = None

    @classmethod
    def get_connection(cls):
        """
        Get an active connection to the RDS instance. If no connection exists or the connection
        is closed, create a new one.

        Returns:
            psycopg2.extensions.connection: A connection object to the RDS instance.
        """
        if cls._connection is None or cls._connection.closed != 0:
            cls._connection = cls.create_connection()
        return cls._connection

    @classmethod
    def create_connection(cls):
        """
        Create a new connection to the RDS instance using credentials retrieved from AWS Secrets Manager.

        Returns:
            psycopg2.extensions.connection: A new connection object to the RDS instance.

        Raises:
            Exception: If the connection to the RDS Proxy cannot be established.
        """
        credentials = cls.get_db_credentials()
        db_username = credentials['username']
        db_password = credentials['password']
        db_name = credentials.get('dbname', 'postgres')
        db_port = int(credentials.get('port', 5432))
        db_host = os.environ.get('RDS_PROXY_ENDPOINT') or credentials.get('host')

        try:
            conn = psycopg2.connect(
                host=db_host,
                user=db_username,
                password=db_password,
                dbname=db_name,
                port=db_port,
                cursor_factory=RealDictCursor,
                connect_timeout=5
            )
            logger.info("SUCCESS: Connection to RDS Proxy succeeded")
            return conn
        except Exception as e:
            logger.error(f"ERROR: Could not connect to RDS Proxy. {e}")
            raise e

    @classmethod
    def get_db_credentials(cls):
        """
        Retrieve database credentials from AWS Secrets Manager.

        Returns:
            dict: A dictionary containing the database credentials (username, password, etc.).

        Raises:
            ClientError: If there is an error retrieving the secret from AWS Secrets Manager.
        """
        AWS_REGION = os.environ.get('AWS_REGION')
        SECRET_NAME = os.environ.get('SECRET_NAME')

        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=AWS_REGION)
        try:
            get_secret_value_response = client.get_secret_value(SecretId=SECRET_NAME)
            secret = get_secret_value_response['SecretString']
            credentials = json.loads(secret)
            return credentials
        except ClientError as e:
            logger.error(f"Error retrieving secret: {e}")
            raise e

    @classmethod
    @log_execution_time
    def execute_query(cls, query, params=None):
        """
        Execute an SQL query, with tenant-specific context.

        Args:
            query (str): SQL query to execute.
            params (tuple, optional): Parameters for the query.

        Returns:
            list: Query results.
        """
        # Retrieve the tenant ID using the get_tenant_id method from common.py
        tenant_id = get_tenant_id()
        if tenant_id is None:
            raise ValueError("tenant_id must be provided to execute the query")

        conn = cls.get_connection()
        try:
            with conn:
                with conn.cursor() as cursor:
                    # Set tenant-specific context in the SQL session
                    logger.info(f"********** RDS SERVICE QUERY STARTING **********")
                    logger.info(f"Executing query: {query}")

                    cursor.execute("SET LOCAL app.current_tenant = %s;", (tenant_id,))
                    cursor.execute(query, params)
                    if cursor.description:
                        result = cursor.fetchall()
                        logger.info(f"Query result: {result}")
                        return result
                    conn.commit()
                    return []
        except Exception as e:
            logger.error(f"ERROR executing query: {e}")
            conn.rollback()
            raise e
        finally:
            logger.info(f"********** RDS SERVICE QUERY FINISHED **********")