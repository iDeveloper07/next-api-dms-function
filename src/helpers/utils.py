import json
from datetime import datetime

from aws_lambda_powertools.utilities.data_classes.api_gateway_proxy_event import (
    APIGatewayProxyEvent,
)


class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for serializing datetime objects.
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
