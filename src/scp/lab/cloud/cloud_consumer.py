#!/usr/bin/env python
# coding=utf-8
import json
import time
import os
import hmac
import base64
from hashlib import sha1
from paho.mqtt import client as mqtt
import logging
import pika
import requests
import dotenv
from typing import Callable, Union
from pathlib import Path
from scp.lab.cloud.base_operator import publish_message


from scp.lab.lab_operator import BaseOperator,BaseParams, ActionResult,StatusMessage

# Set up logging   
logger = logging.getLogger("lab")
logger.setLevel(logging.INFO)
if not logger.handlers:
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Add formatter to ch
    ch.setFormatter(formatter)
    # Add ch to logger
    logger.addHandler(ch)





class BaseConsumer():
    def __init__(self, queue_name,admin, password,host, port,virtual_host):
        super().__init__()
        self.queue_name = queue_name
        self.admin = admin
        self.password = password
        self.host = host    
        self.port = port
        self.virtual_host = virtual_host
        self.connection = None
        self.channel = None
        logging.basicConfig(level=logging.INFO)
  

    def on_message(self, ch, method, properties, body):
        """消息处理逻辑（需子类重写）"""
        raise NotImplementedError

    def run(self, max_retries: int = 0, retry_interval: int = 5):
        """消费者主循环，支持自动重连"""
        retry_count = 0
        while True:
            try:
                credentials = pika.PlainCredentials(self.admin, self.password)
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=self.host,
                    heartbeat=160,
                    blocked_connection_timeout=300,
                    port=self.port,
                    credentials=credentials,
                    virtual_host=self.virtual_host
                ))
                self.connection = connection
                self.channel = connection.channel()
                self.channel.queue_declare(
                    queue=self.queue_name,
                    durable=True,
                    arguments={
                        'x-max-length': 10000,
                        'x-message-ttl': 3600000
                    }
                )
                self.channel.basic_qos(prefetch_count=1)
                self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=self.on_message
                )
                print(f"Consumer {self.queue_name} started, waiting for messages...")
                self.channel.start_consuming()
            except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError) as e:
                print(f"Consumer {self.queue_name} connection error: {str(e)}，{retry_interval}秒后重试...")
                self._cleanup()
                retry_count += 1
                if max_retries and retry_count >= max_retries:
                    print(f"已达到最大重试次数({max_retries})，停止重连。")
                    break
                time.sleep(retry_interval)
            except Exception as e:
                print(f"Consumer {self.queue_name} error: {str(e)}")
                self._cleanup()
                break
            else:
                # 正常退出
                self._cleanup()
                break

    def _cleanup(self):
        """资源清理"""
        if self.channel and self.channel.is_open:
            self.channel.close()
        if self.connection and self.connection.is_open:
            self.connection.close()




# from consumer_base import BaseConsumer

class OrderConsumer(BaseConsumer):
    def __init__(
        self,
        queue_name: str,
        admin: str,
        password: str,
        host: str,
        port: int,
        virtual_host: str,
        registry_url: str,
        device: Union[BaseOperator, Callable[[str, str, BaseParams], ActionResult]]
    ):
        super().__init__(queue_name, admin, password, host, port, virtual_host)

        self.registry_url: str = registry_url
        # Set up device or dispatcher function
        if isinstance(device, BaseOperator):
            self.device = device
            self.dispatch_device_actions = device.dispatch_device_actions
        else:
            self.device = None
            self.dispatch_device_actions = device





    def on_message(self, ch, method, properties, body):
        """处理从 RabbitMQ 收到的消息"""
        request_id = "unknown"
        
        try:
            # 解析消息
            payload = json.loads(body.decode())
            logger.debug(f"Received message: {payload}")
            
            # 提取设备信息
            device_name = payload.get("device_name")
            device_action = payload.get("device_action")
            device_params = payload.get("device_params", {})
            request_id = payload.get("request_id", "unknown")
            
            # 参数校验
            if not device_name or not device_action:
                logger.error(f"Invalid message format: Missing device_name or device_action in request {request_id}")
                ch.basic_ack(delivery_tag=method.delivery_tag)  # 确认消息，不重试无效格式
                return
                
            # 将请求ID添加到参数中
            device_params['request_id'] = request_id
            logger.info(f"Processing request {request_id}: {device_action} on {device_name}")
            
            # 执行设备操作
            if not self.dispatch_device_actions:
                logger.error(f"Request {request_id}: No device action dispatcher function provided")
                ch.basic_ack(delivery_tag=method.delivery_tag)  # 确认消息，配置错误不需要重试
                return
                
            # 调用设备操作
            result = self.dispatch_device_actions(device_name, device_action, device_params)
            result_dict = result.to_dict()
            result_dict["requestId"] = request_id  # 添加请求ID到结果中
            # 准备状态消息
            # status = {
            #     "deviceName": device_name,
            #     "action": device_action,
            #     "requestId": request_id,#兼容设备端
            #     "timestamp": time.time(),
            #     "status": "success",
            #     "result": result_dict
            # }
            
            # 发布状态更新
            push_result = publish_message(self.registry_url, result_dict)
            if push_result:
                logger.info(f"Request {request_id}: Status update published successfully")
            else:
                logger.warning(f"Request {request_id}: Failed to publish status update")
            
            # 确认消息已处理
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug(f"Request {request_id}: Message acknowledged")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {body.decode()[:100]}... Error: {str(e)}")
            ch.basic_ack(delivery_tag=method.delivery_tag)  # 确认消息，无效JSON不需要重试
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {str(e)}", exc_info=True)
            # 对于其他异常，拒绝消息并重新入队
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            logger.info(f"Request {request_id}: Message requeued for retry")


