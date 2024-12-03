import json
import time
from typing import Callable

from aws_lambda_powertools import Logger
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.typing import LambdaContext
from helpers.common import set_tenant_id

logger = Logger()

@lambda_handler_decorator
def middleware_after(
    handler: Callable[[dict, LambdaContext], dict],
    event: dict,
    context: LambdaContext,
) -> dict:
    start_time = time.time()
    response = handler(event, context)
    execution_time = time.time() - start_time

    # Ensure 'headers' exists in the response
    if not isinstance(response, dict):
        response = {'statusCode': 500, 'body': 'Internal server error', 'headers': {}}
    if 'headers' not in response:
        response['headers'] = {}

    # Add custom headers
    response['headers']['execution_time'] = str(execution_time)
    response['headers']['aws_request_id'] = context.aws_request_id

    # Log the execution time
    logger.info(f"Execution time: {execution_time} seconds")

    return response

@lambda_handler_decorator
def tenant_id_middleware(handler, event, context):
    try:
        headers = event.get('headers', {})
        tenant_id = headers.get('coid')
        if not tenant_id:
            logger.error("Missing coid (tenant id) in headers")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing coid in headers'})
            }
        set_tenant_id(tenant_id)
        return handler(event, context)
    except Exception as e:
        logger.exception(f"Exception in tenant_id_middleware. Exception: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }