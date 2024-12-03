from services.rds_service import RDSService
from helpers.common import get_tenant_id
from aws_lambda_powertools import Logger

logger = Logger()

class Tenant:
    def __init__(self, wasabi_sub_account_num=None, wasabi_sub_account_name=None, password=None, access_key=None, secret_key=None):
        self.tenant_id = get_tenant_id()
        self.wasabi_sub_account_num = wasabi_sub_account_num
        self.wasabi_sub_account_name = wasabi_sub_account_name
        self.password = password
        self.access_key = access_key
        self.secret_key = secret_key

    def save(self):
        """
        Save the current Tenant object to the RDS database.
        """
        try:
            insert_query = """
                INSERT INTO Tenants (wasabiSubAccountNum, wasabiSubAccountName, password, accessKey, secretKey)
                VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s, %s)
                ON CONFLICT (tenantId, wasabiSubAccountNum) DO NOTHING;
            """
            params = (
                self.wasabi_sub_account_num,
                self.wasabi_sub_account_name,
                self.password,
                self.access_key,
                self.secret_key
            )
            RDSService.execute_query(insert_query, params)
            logger.info(f"Tenant {get_tenant_id()} saved successfully.")
        except Exception as e:
            logger.error(f"Error saving tenant {get_tenant_id()}: {str(e)}")
            raise e

    @classmethod
    def get_tenant_keys(cls):
        """
        Retrieve tenant's access key and secret key from the RDS database.

        Args:
            tenant_id (str): The tenant's ID.

        Returns:
            Tenant: Tenant object containing access and secret keys, or raises an error if not found.
        """
        try:
            # Query to fetch tenant's access and secret key
            select_query = "SELECT accessKey, secretKey FROM Tenants"
            result = RDSService.execute_query(select_query)

            logger.info(f"Result: {result}")    
            if result:
                tenant_data = result[0]
                return cls(
                    access_key=tenant_data["accesskey"],
                    secret_key=tenant_data["secretkey"]
                )
            else:
                raise ValueError(f"Tenant with ID {get_tenant_id()} not found.")
        except Exception as e:
            logger.error(f"Error retrieving tenant keys for tenant {get_tenant_id()}: {str(e)}")
            raise e
