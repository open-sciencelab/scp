"""
Device base class.

This module contains the Device base class that users can extend
to implement device-specific functionality.
"""
from paho.mqtt import client as mqtt
import json
import inspect
from typing import Dict, Callable, Set, cast, Any, get_type_hints, Type,Optional
from functools import wraps
from inspect import Parameter, Signature
from .types import BaseParams, ActionResult,StatusMessage,DeviceStatus
import logging
import scp.lab.cloud.cloud_devices as cloud_devices
import time
import requests

# from scp.lab.cloud.mqtt_device_twin import get_device_cloud_instance

logger = logging.getLogger("lab")


#Device name registry for internal use
_ACTION_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {}
_DEVICE_NAME_REGISTRY: Dict[str, str] = {}


#Agent name registry for internal use
_AGENT_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {}
_AGENT_NAME_REGISTRY: Dict[str, str] = {}



#Data name registry for internal use
_DATA_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {}
_DATA_NAME_REGISTRY: Dict[str, str] = {}


# Registry for SCP tools  对外注册函数。可以外部进行访问
_SCP_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {}
_SCP_NAME_REGISTRY: Dict[str, str] = {}



def scp_register(scp_action: str):
    """Decorator to register a method as a device action and SCP tool.
    
    This decorator captures the method's signature, including parameter types,
    and stores it in the action registry for use by both the device twin
    and the SCP server.
    
    Args:
        device_action: The name of the action
        
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
        
        def scp_register_action(cls):
            logger.info(f"SCP Registering action {scp_action} for class {cls.__name__}")
            nonlocal cls_name
            cls_name = cls.__name__
            if cls_name not in _SCP_REGISTRY:
                _SCP_REGISTRY[cls_name] = {}
            _SCP_REGISTRY[cls_name][scp_action] = metadata
            return cls
        
        setattr(wrapper, 'scp_register', scp_register_action)
        
        return cast(Callable, wrapper)
    return decorator




class BaseOperator:
    """Base class for base implementations.
    This class provides a mechanism to register actions
    """
    device_name: str = ""
    
    def __init__(self):
        """Initialize the device."""
        self._register_actions()
        # self.mqtt_client = self.get_mqtt_instance()
        # self.mqtt_client = get_device_cloud_instance()
    

    def _register_actions(self):
        """Register all action methods in the registry."""

        for name, method in inspect.getmembers(self.__class__):
            if hasattr(method, 'device_register'):
                method.device_register(self.__class__)
                _DEVICE_NAME_REGISTRY[self.__class__.__name__] = self.device_name

            if hasattr(method, 'scp_register'):
                method.scp_register(self.__class__)
                _SCP_NAME_REGISTRY[self.__class__.__name__] = self.device_name


            if hasattr(method, 'data_register'):
                method.data_register(self.__class__)
                _DATA_REGISTRY[self.__class__.__name__] = self.device_name
                _DATA_NAME_REGISTRY[self.__class__.__name__] = self.device_name

            
            if hasattr(method, 'agent_register'):
                method.agent_register(self.__class__)
                _AGENT_REGISTRY[self.__class__.__name__] = self.device_name
                _AGENT_NAME_REGISTRY[self.__class__.__name__] = self.device_name


   
    
    def dispatch_device_actions(self,device_name: str, device_action: str, device_params: BaseParams) -> ActionResult:
        """Dispatch a device action.
        
        Args:
            device_name: The name of the device
            device_action: The action to perform
            device_params: Parameters for the action
            
        Returns:
            Result of the action
        """


        if device_name != self.device_name:
            return ActionResult(requestId=device_params.get("request_id",""), index=0, messageStatus=-1, message=f"Unknown device: {device_name}").to_dict()

        cls_name = self.__class__.__name__
        
        if cls_name in _ACTION_REGISTRY and device_action in _ACTION_REGISTRY[cls_name]:
            action_metadata = _ACTION_REGISTRY[cls_name][device_action]
            action_func = action_metadata['func']
            
            try:
                logger.info(f"Executing action {device_action} with params {device_params}")
                return action_func(self, device_params)
            except Exception as e:
                return ActionResult(requestId=device_params.get("request_id",""), index=0, messageStatus=-1,message=f"Error executing action {device_action}: {str(e)}").to_dict()
            
        elif cls_name in _AGENT_REGISTRY and device_action in _AGENT_REGISTRY[cls_name]:
            action_metadata = _AGENT_REGISTRY[cls_name][device_action]
            action_func = action_metadata['func']
            
            try:
                logger.info(f"Executing action {device_action} with params {device_params}")
                return action_func(self, device_params)
            except Exception as e:
                return ActionResult(requestId=device_params.get("request_id",""), index=0, messageStatus=-1,message=f"Error executing action {device_action}: {str(e)}").to_dict()

        elif cls_name in _DATA_REGISTRY and device_action in _DATA_REGISTRY[cls_name]:
            action_metadata = _DATA_REGISTRY[cls_name][device_action]
            action_func = action_metadata['func']
            
            try:
                logger.info(f"Executing action {device_action} with params {device_params}")
                return action_func(self, device_params)
            except Exception as e:
                return ActionResult(requestId=device_params.get("request_id",""), index=0, messageStatus=-1,message=f"Error executing action {device_action}: {str(e)}").to_dict()
        else:
            return ActionResult(requestId=device_params.get("request_id",""), index=0, messageStatus=-1, message=f"Unknown action: {device_action}").to_dict()

    @classmethod
    def get_available_actions(cls) -> Set[str]:
        """Get the set of available actions for this device.
        
        Returns:
            Set of action names
        """
        cls_name = cls.__name__
        if cls_name in _ACTION_REGISTRY:
            return set(_ACTION_REGISTRY[cls_name].keys())
        return set()


def register_scp_tools(scp, device: BaseOperator):
    """Register actions for the specified device_name as SCP tools.
    
    This function dynamically creates SCP tools for actions that belong to
    the device class that handles the specified device_name.
    
    Args:
        scp: The SCP server instance
        device: The device to register tools for
    """
    import logging
    
    logger = logging.getLogger("SCP")
    mq_device = cloud_devices.get_device_cloud_instance()
    device_name = device.device_name
    logger.info(f"Registering SCP tools for device_name: {device_name}: {_SCP_NAME_REGISTRY}")
    logger.info(f"Available device classes: {_SCP_REGISTRY.keys()}")
    
    # Find device classes that handle this device_name
    target_cls_names = []
    for cls_name, registered_device_name in _SCP_NAME_REGISTRY.items():
        if registered_device_name == device_name:
            target_cls_names.append(cls_name)
            logger.info(f"Found device class {cls_name} for device_name: {device_name}")
    
    if not target_cls_names:
        logger.warning(f"No device class found for device_name: {device_name}")
        logger.info(f"Available device classes: {list(_SCP_REGISTRY.keys())}")
        logger.info(f"Registered device names: {_SCP_NAME_REGISTRY}")
        return
    
    for target_cls_name in target_cls_names:
        if target_cls_name in _SCP_REGISTRY:
            actions = _SCP_REGISTRY[target_cls_name]
            logger.info(f"Registering {len(actions)} actions for device class {target_cls_name}")
            
            for action_name, metadata in actions.items():
                # First create the parameter signature for the function
                parameters = []
                for param_name, param_info in metadata['params'].items():
                    parameters.append(
                        Parameter(
                            name=param_name,
                            kind=Parameter.POSITIONAL_OR_KEYWORD,
                            annotation=Optional[param_info['type']],
                            default=None 
                        )
                    )
                # 创建新的函数签名
                new_sig = Signature(
                    parameters=parameters,
                    return_annotation=Dict[str, Any]  # 指定返回类型
                )
                
                logger.info(f"Creating SCP tool: {action_name} for device {device_name} with parameters {parameters}")
                # 创建一个工厂函数来确保每个工具函数都有自己的 action_name 和 metadata
                def create_tool_wrapper(current_action_name, current_metadata,current_sig):
                    async def tool_func(**kwargs):
                        """动态创建的SCP工具函数"""
                        params = {}
                        response = {}
                        # 从kwargs中提取参数
                        for param_name in current_metadata['params'].keys():
                            if param_name in kwargs and kwargs[param_name] is not None:
                                params[param_name] = kwargs[param_name]

                        # 检查并添加 request_id
                        if 'request_id' not in params:
                            params['request_id'] = None
                        
                        request_id = mq_device.send_device_control(
                            device_name=device_name,
                            device_action=current_action_name,
                            device_params=params
                        )

                        if request_id:
                            if not  params.get('async_flag', False):
                                # 如果是同步操作，等待结果返回
                                result = mq_device.wait_for_status_update(request_id)
                                if result:
                                    return ActionResult(message="success",messageStatus=1,index = 0,result=result,requestId=request_id).to_dict()
                                else:
                                    return ActionResult(requestId=request_id,messageStatus=2,index = 0,message="同步结果获取失败，通过异步方式获取").to_dict()
                            else:
                                return ActionResult(requestId=request_id,messageStatus=2,index = 0,message="异步操作已提交，请通过状态更新获取结果").to_dict()
                        else:
                             return ActionResult(message="mqtt is not work.",messageStatus=-1,index = 0,requestId=request_id).to_dict()

                    # 设置函数属性
                    tool_func.__name__ = current_action_name
                    tool_func.__doc__ = current_metadata['doc']
                    tool_func.__signature__ = new_sig
                    
                    return tool_func
                
                # 使用工厂函数创建工具函数
                tool_func = create_tool_wrapper(action_name, metadata, new_sig)
                logger.info(f"注册SCP工具: {action_name} 用于设备 {device_name}")
                scp.tool()(tool_func)
        else:
            logger.warning(f"No actions found for device class {target_cls_name}")
