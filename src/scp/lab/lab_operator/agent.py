"""
Device base class.

This module contains the Device base class that users can extend
to implement device-specific functionality.
"""
import inspect
from typing import Dict, Callable, Set, cast, Any, get_type_hints, Type

import logging
from  .base import BaseOperator,_AGENT_REGISTRY
from functools import wraps
from .types import BaseParams, ActionResult
from inspect import Parameter, Signature

logger = logging.getLogger("lab")


def agent_action(action: str):
    """Decorator to register a method as a device action and SCP tool.
    
    This decorator captures the method's signature, including parameter types,
    and stores it in the action registry for use by both the device twin
    and the SCP server.
    
    Args:
        action: The name of the action
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, params: BaseParams) -> ActionResult:
            return func(self, params)
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        param_info = {}
        for param_name, param in list(sig.parameters.items())[1:]:  # Skip 'self'
            if param_name == 'params' and param.annotation != inspect.Parameter.empty:
                param_class = param.annotation
                if hasattr(param_class, '__annotations__'):
                    for field_name, field_type in param_class.__annotations__.items():
                        param_info[field_name] = {
                            'type': field_type,
                            'required': True,  # Assume required by default
                            'description': f"Parameter: {field_name}"
                        }
        
        return_type = type_hints.get('return', None)
        
        metadata = {
            'func': func,
            'params': param_info,
            'return_type': return_type,
            'doc': func.__doc__
        }
        
        cls_name = None
        
        def register_action(cls):
            logger.info(f"Agent Action Internal Register {action} for class {cls.__name__}")
            nonlocal cls_name
            cls_name = cls.__name__
            if cls_name not in _AGENT_REGISTRY:
                _AGENT_REGISTRY[cls_name] = {}
            _AGENT_REGISTRY[cls_name][action] = metadata
            return cls
        
        setattr(wrapper, 'agent_register', register_action)
        
        return cast(Callable, wrapper)
    return decorator