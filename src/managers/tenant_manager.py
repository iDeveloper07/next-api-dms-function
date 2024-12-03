from aws_lambda_powertools import Logger
from models.tenant_model import Tenant
from services.wasabi_service import WasabiService
from helpers.common import get_tenant_id
from services.logging_service import log_execution_time

logger = Logger()

class TenantManager:
    
    @staticmethod
    @log_execution_time
    def get_tenant_keys():
        """
        Retrieve tenant's access key and secret key using the Tenant model.
        
        Args:
            tenant_id (str): The tenant's ID.
        
        Returns:
            dict: Tenant's access key and secret key.
        """
        try:
            tenant_id = get_tenant_id()
            logger.info(f"Fetching tenant keys for tenant ID: {tenant_id}.")
            tenant = Tenant.get_tenant_keys()
            
            return {
                "accessKey": tenant.access_key,
                "secretKey": tenant.secret_key
            }
        except Exception as e:
            logger.error(f"Error retrieving tenant keys for tenant {tenant_id}: {str(e)}")
            raise e
        
    
    @staticmethod
    @log_execution_time
    def create_tenant(data):
        """
        Creates a new tenant and saves the details to RDS using the Tenant model.
        
        Args:
            tenant_data (dict): Dictionary containing tenant details.
        
        Returns:
            Tenant: The created Tenant object.
        """
        try:
            tenant_id = get_tenant_id()
            logger.info(f"Creating tenant with ID: {tenant_id}.")

            quota = data.get("quota", 1024)
            isTrial = data.get("isTrial", True)
            enable_ftp = data.get("enableFtp", False)

            wasabi_details = WasabiService.create_wasabi_subaccount(data["account_name"], quota, isTrial, enable_ftp)
            logger.info(f"Wasabi subaccount created: {wasabi_details}")

            # Create Tenant object
            new_tenant = Tenant(
                wasabi_sub_account_num=wasabi_details["account_number"],
                wasabi_sub_account_name=wasabi_details["account_name"],
                password=wasabi_details["password"],
                access_key=wasabi_details["access_key"],
                secret_key=wasabi_details["secret_key"]
            )

            # Save to RDS
            new_tenant.save()
            logger.info(f"Tenant {tenant_id} saved successfully.")

            return new_tenant

        except Exception as e:
            logger.error(f"Error creating tenant: {str(e)}")
            raise e