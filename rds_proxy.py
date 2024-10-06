import os
import json
import logging
import psycopg2
import boto3
from botocore.exceptions import ClientError

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global variable to hold the database connection
connection = None

# Get the required parameters from environment variables
AWS_REGION = os.environ.get('AWS_REGION')
RDS_PROXY_ENDPOINT = os.environ.get('RDS_PROXY_ENDPOINT')
DB_PORT = int(os.environ.get('DB_PORT', '5432'))  # Default to 5432 if not set
SECRET_NAME = os.environ.get('SECRET_NAME')
IS_DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

if IS_DEBUG:
    logger.setLevel(logging.DEBUG)

def get_db_credentials():
    """Retrieve database credentials from AWS Secrets Manager."""
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

def create_rds_connection():
    global connection
    if connection is None or connection.closed != 0:
        # Retrieve database credentials
        credentials = get_db_credentials()
        db_username = credentials['username']
        db_password = credentials['password']
        db_name = credentials.get('dbname', 'postgres')
        db_port = int(credentials.get('port', DB_PORT))
        db_host = RDS_PROXY_ENDPOINT or credentials.get('host')

        try:
            # Connect to the database via RDS Proxy
            connection = psycopg2.connect(
                host=db_host,
                user=db_username,
                password=db_password,
                dbname=db_name,
                port=db_port,
                connect_timeout=5
            )
            logger.info("SUCCESS: Connection to RDS Proxy succeeded")
        except Exception as e:
            logger.error(f"ERROR: Could not connect to RDS Proxy. {e}")
            raise e

def execute_query(query, data=None):
    try:
        if connection is None or connection.closed != 0:
            create_rds_connection()

        with connection.cursor() as cursor:
            cursor.execute(query, data)
            connection.commit()
            if cursor.description:
                results = cursor.fetchall()
                return results
            else:
                return None
        # Do not close the connection if you intend to reuse it
        return results
    except Exception as e:
        logger.error(f"ERROR executing query: {e}")
        return []
    
