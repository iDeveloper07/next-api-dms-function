import json
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

from middleware import middleware_after, tenant_id_middleware
from utils import DateTimeEncoder  # Import the custom DateTimeEncoder

logger = Logger()
app = APIGatewayRestResolver()

from handlers.activity import *
from handlers.tenant import *
from handlers.user import *
from handlers.document import *
from handlers.tag import *
from handlers.workflow import *
from handlers.policy import *


@middleware_after
@tenant_id_middleware
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    response = app.resolve(event, context)

    if "body" in response and isinstance(response["body"], dict):
        response["body"] = json.dumps(response["body"], cls=DateTimeEncoder)

    return response
