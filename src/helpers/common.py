import threading
from aws_lambda_powertools import Tracer

_local_data = threading.local()

def set_tenant_id(tenant_id: str) -> None:
    """
    Stores the tenant_id in Tracer annotations to make it globally accessible for the request.

    Args:
        tenant_id (str): The tenant ID to store.
    """
    _local_data.tenant_id = tenant_id


def get_tenant_id() -> str:
    """
    Retrieves the tenant_id from the Tracer annotations.

    Returns:
        str: The tenant ID if set; otherwise, None.
    """
    
    return getattr(_local_data, "tenant_id", None)  
