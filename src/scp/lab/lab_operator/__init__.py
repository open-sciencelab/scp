"""
Device module for science-agent-sdk.
This module provides base device functionality.
"""

from .base import BaseOperator,scp_register
from .device import device_action
from .agent import agent_action


from .types import BaseParams, ActionResult,DeviceParams,AgentParams,StatusMessage,DeviceStatus

__all__ = [
    'BaseOperator',
    'BaseParams',
    'ActionResult',
    'DeviceParams',
    'AgentParams',
    'device_action',
    'agent_action',
    'scp_register',
    'StatusMessage',
    'DeviceStatus'

] 