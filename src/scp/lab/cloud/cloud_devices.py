
import pika
import sys
import uuid
import time
import json
import logging
from typing import Dict, Any, Optional
from scp.lab.cloud.base_operator import get_message
logger = logging.getLogger("cloud")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    

class DeviceControlSender:
    def __init__(self, admin:str, password:str , queue_name:str , host:str , port:int , virtual_host:str , registry_url:str):   
        self.admin = admin
        self.password = password
        self.queue_name = queue_name
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.registry_url = registry_url

    def send_device_control(self, 
                     device_name: str, 
                     device_action: str, 
                     device_params: Optional[Dict[str, Any]] = None) -> str:
        """Send a device control message.
        
        Args:
            device_name: 设备名称
            device_action: 设备动作
            device_params: 设备参数
            
        Returns:
            str: 请求ID
        """
        # 参数检查与默认值设置
        if not device_name or not device_action:
            raise ValueError("设备名称和动作不能为空")
        
        if device_params is None:
            device_params = {}
        
        request_id = str(uuid.uuid4())
        
        # 准备消息负载
        payload = {
            "request_id": request_id,
            "device_name": device_name,
            "device_action": device_action,
            "device_params": device_params,
            "timestamp": time.time()
        }
        
        connection = None
        try:
            # 创建连接
            credentials = pika.PlainCredentials(self.admin, self.password)
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=self.host,
                heartbeat=600,
                blocked_connection_timeout=300,
                port=self.port,
                credentials=credentials,
                virtual_host=self.virtual_host,
                # 添加重连参数
                connection_attempts=3,
                retry_delay=5
            ))
            
            channel = connection.channel()

            # 声明持久化队列
            channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={
                    'x-max-length': 10000,
                    'x-message-ttl': 3600000,
                    # 'x-max-priority': 10
                }
            )
            
            # 序列化消息体
            message_body = json.dumps(payload)
            
            # 发送持久化消息
            channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 消息持久化
                    priority=1,       # 消息优先级
                    content_type='application/json',
                    timestamp=int(time.time())
                )
            )
            
            logging.info(f"Request {request_id}: 已发送控制命令 '{device_action}' 到设备 '{device_name}'")
            return request_id
            
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"RabbitMQ 连接错误: {str(e)}")
            raise
        except pika.exceptions.ChannelError as e:
            logging.error(f"RabbitMQ 通道错误: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"发送设备控制消息时出错: {str(e)}")
            raise
        finally:
            # 确保连接关闭
            if connection and connection.is_open:
                connection.close()
    

    def wait_for_status_update(self, request_id: str, timeout: float = 20.0) -> Optional[Dict[str, Any]]:
        """Wait for a status update for a specific request.
        
        Args:
            request_id: 请求ID
            timeout: 超时时间（秒）
            
        Returns:
            Optional[Dict[str, Any]]: 状态更新或None（如果超时）
        """
        start_time = time.time()
        elapsed_time = 0
        
        while elapsed_time < timeout:
            # 获取消息
            if request_id:
                result = get_message(self.registry_url, request_id)
                if result:
                    logger.info(f"Received result for request {request_id}: {result}")
                    
                    # # 更新挂起的请求状态
                    # if request_id in self.pending_requests:
                    #     self.pending_requests[request_id]["response"] = result
                    #     self.pending_requests[request_id]["completed"] = True
                    
                    return result

            # 等待2秒后再次尝试
            time.sleep(2)
            elapsed_time = time.time() - start_time
            logger.info(f"Waiting for result... Elapsed time: {elapsed_time:.1f}s")
        
        logger.warning(f"Timeout waiting for result for request {request_id}")
        return None


_device_cloud_instance = None

def get_device_cloud_instance( admin:str =None, password:str =None, queue_name:str =None, host:str =None, port:int =None, virtual_host:str =None, registry_url:str =None):
    """Get the global Device Cloud instance.
    
    Returns:
        DeviceCloud: 全局Device Cloud实例
    """
    global _device_cloud_instance
    if _device_cloud_instance is None :
        if admin is None:
            return None
        else:
            _device_cloud_instance = DeviceControlSender(admin, password, queue_name, host, port, virtual_host, registry_url)
    return _device_cloud_instance

if __name__ == '__main__':
    queue_name ='task_queue'
    for i in range(10):
        publish_message("admin","louwenjie",queue_name, f"Message {i} with priority {i%3}")