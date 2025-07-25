"""
Message wrapper with metadata support.

This module defines a wrapper type that combines JSONRPCMessage with metadata
to support transport-specific features like resumability.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from scp.types import JSONRPCMessage, RequestId

ResumptionToken = str

ResumptionTokenUpdateCallback = Callable[[ResumptionToken], Awaitable[None]]


@dataclass
class ClientMessageMetadata:
    """Metadata specific to client messages."""

    resumption_token: ResumptionToken | None = None
    on_resumption_token_update: Callable[[ResumptionToken], Awaitable[None]] | None = (
        None
    )


@dataclass
class ServerMessageMetadata:
    """Metadata specific to server messages."""

    related_request_id: RequestId | None = None


MessageMetadata = ClientMessageMetadata | ServerMessageMetadata | None


@dataclass
class SessionMessage:
    """A message with specific metadata for transport-specific features."""

    message: JSONRPCMessage
    metadata: MessageMetadata = None
