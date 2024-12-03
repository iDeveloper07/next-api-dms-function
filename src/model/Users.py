from rds_proxy import execute_query
import logging

logger = logging.getLogger()


def mu_get_user_key(tenant_id, user_id):
    # check if this user is tenant root admin
    search_query = "SELECT accessKey, secretKey FROM Tenants WHERE tenantId = %s AND wasabiSubAccountId = %s LIMIT 1;"
    results = execute_query(search_query, (tenant_id, user_id))

    logger.info(f"**************Getting Tenant Keys**************results: {results}")

    all_tenants = "SELECT * FROM Tenants;"
    res = execute_query(all_tenants)
    logger.info(f"*******************ALL Tenants**************results: {res}")


    if not results:
        search_query = "SELECT accessKey, secretKey FROM Users WHERE tenantId = %s AND userName = %s LIMIT 1;"
        results = execute_query(search_query, (tenant_id, user_id))

    if results:
        return {"accessKey": results[0][0], "secretKey": results[0][1]}
    else:
        return False
