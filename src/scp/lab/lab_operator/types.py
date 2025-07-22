"""
Type definitions for device operations.

This module contains base type definitions for device operations,
including input and output types for device actions.
"""
from typing import Dict, Any, TypedDict,Literal,List
from enum import Enum
class ActionResult:
    """Base class for all action results."""

    def __init__(self,message: str, requestId: str = "", index: int = 0, result: Any = None, method: str = "",messageStatus:int =0):
        """Initialize the action result.
        
        Args:
            message: Human-readable message
            requestId: Unique identifier for the action request
            index: Step index in the action sequence
            result: Result of the action, can be any type
            method: Name of the action method
            messageStatus: Status of the message, e.g., 1 for final result,
                          2 for intermediate result, -1 for error, etc.
        """
  
        self.message = message #人类可读的消息
        self.requestId = requestId  #操作实
        self.index = index    #步骤序列号  0,1,2,3.etc
        self.result = result #操作结果 
        self.method = method #操作方法名称
        self.messageStatus = messageStatus   #messageStatus: 1 for 最终结果, 2 for 中间结果, -1 for 错误, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.
        
        Returns:
            Dictionary representation of the result
        """
        return {
            "message": self.message,
            "requestId": self.requestId,
            "index": self.index,
            "result": self.result,
            "method": self.method,
            "messageStatus":self.messageStatus
        }


# class SuccessResult(ActionResult):
#     """Success result with data."""

#     def __init__(self, message: str, data: Any = None, request_id: str = ""):
#         """Initialize the success result.
        
#         Args:
#             message: Human-readable message
#             data: Data returned by the action
#         """
#         super().__init__("success", message)
#         self.data = data
#         self.request_id =   request_id # Optional request ID, can be set later
    
#     def to_dict(self) -> Dict[str, Any]:
#         """Convert the result to a dictionary.
        
#         Returns:
#             Dictionary representation of the result
#         """
#         return {
#             "status": self.status,
#             "message": self.message,
#             "data": self.data,
#             "request_id": self.request_id
#         }

# class ErrorResult(ActionResult):
#     """Error result."""
    
#     def __init__(self, message: str):
#         """Initialize the error result.
        
#         Args:
#             message: Human-readable message
#         """
#         super().__init__("error", message)

from datetime import date




class DeviceStatus(Enum):
    """设备状态枚举类"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    SUCCESS = "success"      # 执行成功
    ERROR = "error"         # 执行错误
    TIMEOUT = "timeout"     # 执行超时
    CANCELLED = "cancelled" # 已取消
    
class StatusMessage(TypedDict, total=False):
    device_name: str
    action: str
    request_id: str
    result: Dict[str, Any]
    timestamp: date
    status: DeviceStatus
# UUID: str
# 表示调用实例的唯一标识符。
# 类型为字符串。

# user_id: str
# 用户 ID，用于鉴权。
# 类型为字符串。

# organization_id: str
# 机构 ID，用于鉴权。
# 类型为字符串。

# creat_time: date
# 创建时间。
# 类型为 datetime.date。

# experiment_type: Literal["干", "湿实验", "干湿结合"]
# 实验类型，限定为枚举值 "干"、"湿实验" 或 "干湿结合"。
# 使用 Literal 定义枚举类型。

# experiment_name: str
# 实验名称。
# 类型为字符串。

# experiment_des: str
# 实验描述。
# 类型为字符串。

# priority: Literal["高", "中", "低"]
# 优先级，限定为枚举值 "高"、"中" 或 "低"。
# 使用 Literal 定义枚举类型。

class BaseParams(TypedDict, total=False):
    """Base class for all parameter types."""
    user_id: str  # 用户ID【鉴权】
    organization_id: str  # 机构ID【鉴权】
    creat_time: date  # 创建时间
    experiment_type: Literal["dry-experiment", "wet-experiment", "dry-wet-experiment"]  # 实验类型【枚举】
    experiment_name: str  # 实验名称
    experiment_des: str  # 实验描述
    priority: Literal["high", "med", "low"]  # 优先级【枚举】
    request_id: str  #操作实例
    async_flag: bool  # 是否异步执行

# device_name: str 
# 描述设备的名称，格式为 [实验室名称+内部分类+具体功能]。
# 类型为字符串。

# device_id: str
# 设备的唯一编码。
# 类型为字符串。

# device_des: str
# 对设备的描述信息。
# 类型为字符串。

# customized_params: List[Any]
# 设备的定制参数列表。
# 类型为 List[Any]，可以根据需求进一步细化为具体类型。

class DeviceParams(BaseParams, total=False):
    """Base class for all device parameter types."""
    device_name: str  # 实验室名称+内部分类+具体功能
    device_id: str  # 设备编码
    device_des: str  # 设备描述
    customized_params: List[Any]  # 设备定制参数

# api_key: str 
# 设备调用秘钥，用于外部模型的鉴权。
# 类型为字符串。
# 可选字段。

# agent_name: str
# 智能体的名称，格式为 [实验室名称+内部分类+具体功能]。
# 类型为字符串。

# agent_id: str
# 智能体的唯一编码。
# 类型为字符串。

# agent_des: str
# 对智能体的描述信息。
# 类型为字符串。

# customized_params: List[Any]
# 智能体的定制参数列表。
# 类型为 List[Any]，可以根据需求进一步细化为具体类型。

class AgentParams(BaseParams, total=False):
    """Base class for all lab agent parameter types."""
    api_key: str  # 设备调用秘钥【针对外部模型，可选】
    agent_name: str  # 实验室名称+内部分类+具体功能
    agent_id: str  # 智能体编码
    agent_des: str  # 智能体描述
    customized_params: List[Any]  # 设备定制参数
