import time
from typing import Callable

from aws_lambda_powertools import Logger
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.typing import LambdaContext


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

    # Adding custom headers in response object after Lambda execution
    if isinstance(response, dict) and "headers" in response:
        response["headers"]["execution_time"] = str(execution_time)
        response["headers"]["aws_request_id"] = context.aws_request_id
    else:
        # If the response doesn't have headers, log a warning
        logger.warning("Response object does not have 'headers' to add execution_time and aws_request_id.")

    # Log the execution time
    logger.info(f"Execution time: {execution_time} seconds")

    return response
