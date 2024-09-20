import boto3
import psycopg2
from os import environ

from aws_lambda_powertools import Logger

logger = Logger()
client = boto3.client('rds')  # Get the rds object

# Get the required parameters to create a token
# Get the RDS proxy endpoint,  By default, all proxy connections have read/write capability and use the writer instance. 
# To connect to the read replica only, create an additional RDS proxy endpoint and specify TargetRole to READ_ONLY.
aws_region = environ.get('REGION')                  # Get the AWS region
proxy_endpoint = environ.get('RDS_PROXY_ENDPOINT')  # Get the RDS proxy endpoint
db_port = environ.get('DB_PORT')                    # Get the database port
db_username = environ.get('DB_USERNAME')            # Get the database username
db_password = environ.get('DB_PASSWORD')            # Get the database password
database = environ.get('DB_NAME')                   # Get the database name 
is_debug = environ.get('DEBUG')                     # Is debug mode enabled


# Create RDS Connection
def create_rds_connection():
    try:
        token = db_password
        if is_debug != 'True':
            # Generate the authentication token -- temporary password
            token = client.generate_db_auth_token(
                DBHostname=proxy_endpoint,
                Port=db_port,
                DBUsername=db_username,
                Region=aws_region
            )

        # Create an RDS connection object
        connection = psycopg2.connect(
            host=proxy_endpoint,
            database=database,
            port=db_port,
            user=db_username,
            password=token,
        )
    except Exception as e:
        logger.error("Failed to create database connection due to {}".format(e))
        return e

    return connection


def execute_query(query, data=None):
    """
    Executes the given SQL query on the RDS database and returns the results.

    Args:
        query (str): The SQL query to execute.
        data (tuple, optional): The data to be passed as parameters to the query.

    Returns:
        list: The results of the query as a list of tuples.

    """
    try:
        conn = create_rds_connection()
        cursor = conn.cursor()
        cursor.execute(query, data)
        results = cursor.fetchall()
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(e)
        results = []
    return results
