import time
from aws_lambda_powertools import Logger

logger = Logger()

def log_execution_time(method):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = method(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"Method {method.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper