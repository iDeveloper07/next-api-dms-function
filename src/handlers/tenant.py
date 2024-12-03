import json
from app import app
from managers.tenant_manager import TenantManager
from managers.user_manager import UserManager
from services.rds_service import RDSService
from aws_lambda_powertools import Logger

logger = Logger()

@app.post("/tenants")
def create_tenant():
    """
    Create a new tenant and save it to the RDS database.
    
    Returns:
        dict: JSON response indicating success or failure of the operation.
    """
    try:
        data = app.current_event.json_body

        # Validate required fields
        required_fields = ["account_name"]
        if not all(data.get(field) for field in required_fields):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        # Call the tenant manager to create the tenant
        tenant = TenantManager.create_tenant(data)

        seed_user_id = data.get("seed_user_id", None)
        if seed_user_id:
            logger.info(f"Creating seed user {seed_user_id} for tenant {tenant.tenant_id}")
            user = UserManager.get_or_create_user(user_name=seed_user_id, is_admin=True)

            if user:
                logger.info(f"Seed user {user.get("userName")} created successfully for tenant {tenant.tenant_id}")
            else:
                logger.error(f"Failed to create seed user for tenant {tenant.tenant_id}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Failed to create seed user'})
                }
        
        return {
            'statusCode': 201,
            'body': json.dumps({'message': f'Tenant {tenant.tenant_id} created successfully'})
        }

    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

@app.post("/runsetupscript")
def run_sql_script():
    """
    Execute the multi-tenant DMS setup SQL script using RDSService.
    
    Returns:
        dict: JSON response indicating success or failure of the operation.
    """
    try:
        # The SQL script to create and configure the multi-tenant DMS tables
        sql_script = """
        -- Multi-tenant DMS setup and update SQL script

-- Drop tables if they exist in the correct order (handling foreign key dependencies)
DROP TABLE IF EXISTS Activity;         -- Activity depends on Users
DROP TABLE IF EXISTS DocumentTags;     -- DocumentTags depends on Documents and Tags
DROP TABLE IF EXISTS Documents;        -- Documents depend on Tenants
DROP TABLE IF EXISTS Tags;             -- Tags table added
DROP TABLE IF EXISTS Users;            -- Users depend on Tenants
DROP TABLE IF EXISTS Workflow;         -- Workflow depends on Tenants
DROP TABLE IF EXISTS Tenants;          -- Tenants table should be dropped last as others depend on it


-- Enable PostgreSQL extensions if required
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tenants Table
CREATE TABLE Tenants (
    id SERIAL PRIMARY KEY,
    tenantId VARCHAR(255) NOT NULL DEFAULT current_setting('app.current_tenant'),
    wasabiSubAccountNum VARCHAR(255) NOT NULL,
    wasabiSubAccountName VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    accessKey VARCHAR(255) NOT NULL,
    secretKey VARCHAR(255) NOT NULL,
    createdAt TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenantId, wasabiSubAccountNum)
);

-- Users Table
CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    tenantId VARCHAR(255) NOT NULL DEFAULT current_setting('app.current_tenant'),
    userName VARCHAR(255) NOT NULL,
    wasabiUserId VARCHAR(255) NOT NULL,
    wasabiUserArn VARCHAR(255) NOT NULL,
    accessKey VARCHAR(255) NOT NULL,
    secretKey VARCHAR(255) NOT NULL,
    isAdmin BOOLEAN NOT NULL,
    createdAt TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenantId, userName)
);

-- Documents Table
CREATE TABLE Documents (
    id SERIAL PRIMARY KEY,
    tenantId VARCHAR(255) NOT NULL DEFAULT current_setting('app.current_tenant'),
    bucketName VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    key VARCHAR(255) NOT NULL,
    prefix VARCHAR(255) NOT NULL,
    size INT NOT NULL,
    type VARCHAR(255) NOT NULL,
    hash VARCHAR(255) NOT NULL,
    version VARCHAR(255) NOT NULL,
    createdAt TIMESTAMP DEFAULT NOW()
);

-- Tags Table
CREATE TABLE Tags (
    id SERIAL PRIMARY KEY,
    tenantId VARCHAR(255) NOT NULL DEFAULT current_setting('app.current_tenant'),
    tagKey VARCHAR(255) NOT NULL,
    tagValue VARCHAR(255) NOT NULL,
    createdAt TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenantId, tagKey)
);

-- DocumentTags Table (Many-to-Many relationship between Documents and Tags)
CREATE TABLE DocumentTags (
    id SERIAL PRIMARY KEY,
    tenantId VARCHAR(255) NOT NULL DEFAULT current_setting('app.current_tenant'),
    documentId INT NOT NULL REFERENCES Documents(id) ON DELETE CASCADE,
    bucketName VARCHAR(255) NOT NULL,
    tagKey VARCHAR(255) NOT NULL,
    createdAt TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenantId, documentId, tagKey)
);

-- Activity Table
CREATE TABLE Activity (
    id SERIAL PRIMARY KEY,
    tenantId VARCHAR(255) NOT NULL DEFAULT current_setting('app.current_tenant'),
    firstName VARCHAR(255) NOT NULL,
    lastName VARCHAR(255) NOT NULL,
    bucketName VARCHAR(255) NOT NULL,
    folderName VARCHAR(255),
    documentName VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    userName VARCHAR(255) NOT NULL,
    FOREIGN KEY (tenantId, userName) REFERENCES Users(tenantId, userName) ON DELETE CASCADE
);

CREATE TABLE Workflow (
    id SERIAL PRIMARY KEY,
    tenantId VARCHAR(255) NOT NULL DEFAULT current_setting('app.current_tenant'),
    triggerName VARCHAR(255) NOT NULL, 
    projectName VARCHAR(255) NOT NULL, 
    workflowId VARCHAR(50) NOT NULL, 
    bucketName VARCHAR(255) NOT NULL,
    folderPath VARCHAR(255),
    action VARCHAR(10) CHECK (action IN ('CREATE', 'UPDATE', 'DELETE')),    
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enable Row-Level Security for All Tables
ALTER TABLE Tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE Users ENABLE ROW LEVEL SECURITY;
ALTER TABLE Documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE Tags ENABLE ROW LEVEL SECURITY;  
ALTER TABLE DocumentTags ENABLE ROW LEVEL SECURITY;
ALTER TABLE Activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE Workflow ENABLE ROW LEVEL SECURITY;


-- Create Policies for Tenant Isolation

-- Tenant isolation for Tenants table
CREATE POLICY tenant_isolation_tenants ON Tenants
    USING (tenantId = current_setting('app.current_tenant'));

-- Tenant isolation for Users table
CREATE POLICY tenant_isolation_users ON Users
    USING (tenantId = current_setting('app.current_tenant'));

-- Tenant isolation for Documents table
CREATE POLICY tenant_isolation_documents ON Documents
    USING (tenantId = current_setting('app.current_tenant'));

-- Tenant isolation for Tags table
CREATE POLICY tenant_isolation_tags ON Tags
    USING (tenantId = current_setting('app.current_tenant'));

-- Tenant isolation for DocumentTags table (Many-to-Many relationship between Documents and Tags)
CREATE POLICY tenant_isolation_document_tags ON DocumentTags
    USING (tenantId = current_setting('app.current_tenant'));

-- Tenant isolation for Activity table
CREATE POLICY tenant_isolation_activity ON Activity
    USING (tenantId = current_setting('app.current_tenant'));

-- Tenant isolation for Workflow table
CREATE POLICY tenant_isolation_workflow ON Workflow
    USING (tenantId = current_setting('app.current_tenant'));


-- Indexes for Optimized Search

-- Index for faster lookup of documents by bucketName, prefix, and name
CREATE INDEX idx_documents_bucket_prefix ON Documents (bucketName, prefix, name);

-- Index for faster search of document-tag relationships by documentId and tagKey in the DocumentTags table
CREATE INDEX idx_document_tags_document_tag ON DocumentTags (documentId, tagKey);

-- Index for faster retrieval of tags by tagKey and tenantId in the Tags table
CREATE INDEX idx_tags_tenant_tagkey ON Tags (tenantId, tagKey);

-- Index for optimized search of users by tenantId and userName in the Users table
CREATE INDEX idx_users_tenant_username ON Users (tenantId, userName);

-- Index for optimized search of tenants by tenantId in the Tenants table
CREATE INDEX idx_tenants_tenantId ON Tenants (tenantId);


-- Revoke privileges
REVOKE ALL PRIVILEGES ON SCHEMA public FROM dms_manager;
REVOKE ALL PRIVILEGES ON DATABASE mytestdb FROM dms_manager;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM dms_manager;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM dms_manager;
REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM dms_manager;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM dms_manager;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM dms_manager;

-- Drop the role if it already exists (use with caution)
DROP ROLE IF EXISTS dms_manager;

-- Create the role with the specified password
CREATE ROLE dms_manager WITH LOGIN PASSWORD 'W2nm!+9mMkl_!sO]Lg5g)Vyt';

-- Grant all privileges on existing tables in the public schema to the new role
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dms_manager;

-- Grant all privileges on existing sequences in the public schema to the new role
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dms_manager;

-- Ensure the role has privileges on all future tables and sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO dms_manager;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO dms_manager;

-- Grant role usage on the current database
GRANT CONNECT ON DATABASE mytestdb TO dms_manager;

-- Optional: Grant privileges to create new tables (if needed)
GRANT CREATE ON SCHEMA public TO dms_manager;
        """

        # Execute the SQL script
        logger.info("Executing SQL script for multi-tenant DMS setup")
        RDSService.execute_query(sql_script)

        logger.info("SQL script executed successfully.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'SQL script executed successfully'})
        }

    except Exception as e:
        logger.error(f"Failed to execute SQL script: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Failed to execute SQL script: {str(e)}'})
        }
    
@app.post("/execute-sql")
def execute_custom_sql():
    """
    Execute a custom SQL query passed in the request payload.
    
    Returns:
        dict: JSON response containing the result of the SQL execution or an error message.
    """
    try:
        data = app.current_event.json_body
        
        # Extract the SQL query from the request body
        sql_query = data.get("query")
        
        if not sql_query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing SQL query in payload'})
            }

        # Execute the custom SQL query using the RDSService
        logger.info(f"Executing SQL query: {sql_query}")
        result = RDSService.execute_query(sql_query)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'result': result}, default=str)
        }
        
    except Exception as e:
        logger.error(f"Failed to execute SQL query: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }    
