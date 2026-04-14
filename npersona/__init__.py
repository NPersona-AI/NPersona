"""NPersona - AI Security Testing Framework.

A comprehensive framework for adversarial security testing of AI systems.
"""

__version__ = "1.0.4"
__author__ = "NPersona-AI"
__email__ = "hello@npersona.ai"
__license__ = "MIT"

from .client import NPersonaClient
from .config import (
    Config,
    BearerTokenAuth,
    OAuth2Config,
    APIKeyAuth,
    BasicAuth,
    CustomAdapter,
)

__all__ = [
    "NPersonaClient",
    "Config",
    "BearerTokenAuth",
    "OAuth2Config",
    "APIKeyAuth",
    "BasicAuth",
    "CustomAdapter",
]
