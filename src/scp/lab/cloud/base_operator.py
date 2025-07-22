 
from typing import Callable, Dict, Any, Optional
import time
import requests
from scp.lab.lab_operator.types import  StatusMessage,DeviceStatus



def create_status_message(
    device_name: str,
    action: str = "huixiang_plan",
    request_id: Optional[str] = None,
    status: DeviceStatus = DeviceStatus.RUNNING,
    result: Optional[Dict[str, Any]] = None
) -> StatusMessage:
    """创建设备状态消息
    
    Args:
        device_name: 设备名称
        action: 动作名称，默认为 huixiang_plan
        request_id: 请求ID，默认为 None
        status: 设备状态，默认为 RUNNING
        result: 默认为None
        
    Returns:
        StatusMessage: 格式化的状态消息
    """

        
    return {
        "device_name": device_name,
        "action": action,
        "request_id": request_id,
        "timestamp": time.time(),
        "status": status,
        "result": result
    } # type: ignore


def get_message(registry_url:str, request_id: str) -> Optional[StatusMessage]:
    """从注册中心获取状态消息
    
    Args:
        registry_url: 注册中心的URL
        request_id: 请求ID
    
    Returns:
        Optional[StatusMessage]: 状态消息，如果未找到则返回 None
    """
    try:
        response = requests.get(f"{registry_url}/get_server_result/{request_id}")
        if response.status_code == 200:
            return response.json()  # type: ignore
        else:
            print(f"获取状态消息失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"获取状态消息时发生错误: {str(e)}")
        return None
     

def publish_message(registry_url:str, status: StatusMessage) -> bool:


        try:
        
             # 确保状态消息包含时间戳
            if 'timestamp' not in status:
                status['timestamp'] = time.time() # type: ignore
    
            # 将 DeviceStatus 枚举转换为字符串
            if 'status' in status and isinstance(status['status'], DeviceStatus):
                    status['status'] = status['status'].value

        # 发送POST请求
            response = requests.post(
                f"{registry_url}/set_result/",
                json=status,
                headers={"Content-Type": "application/json"}
            )

            # 检查响应
            if response.status_code == 200:
                print(f"状态消息发送成功: {response.status_code} - {response.text}")
                return True
            else:
                print(f"发送失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"发送状态消息时发生错误: {str(e)}")
            return False

