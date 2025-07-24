import pika
import logging
import time


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

    def run(self):
        """消费者主循环"""
        try:
            credentials = pika.PlainCredentials(self.admin, self.password)
            # 建立持久化连接
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=self.host,
                heartbeat=600,  # 防止连接超时
                blocked_connection_timeout=300,
                port=self.port,
                credentials=credentials,
                virtual_host=self.virtual_host  
            ))
            self.channel = connection.channel()
                    
            # 声明持久化队列
            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={
                    'x-max-length': 10000,
                    'x-message-ttl': 3600000
                }
            )
            
            # 设置公平分发
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.on_message
            )
            
            print(f"Consumer {self.queue_name} started, waiting for messages...")
            self.channel.start_consuming()
        except Exception as e:
            print(f"Consumer {self.queue_name} error: {str(e)}")
        finally:
            self._cleanup()

    def _cleanup(self):
        """资源清理"""
        if self.channel and self.channel.is_open:
            self.channel.close()
        if self.connection and self.connection.is_open:
            self.connection.close()




# from consumer_base import BaseConsumer

class OrderConsumer(BaseConsumer):
    def __init__(self, queue_name, admin, password, host, port, virtual_host):
        super().__init__(queue_name, admin, password, host, port, virtual_host)

    def on_message(self, ch, method, properties, body):
        try:
            # 模拟业务处理（带重试机制）
            print(f"Processing: {body}")
            time.sleep(0.5 + hash(body) % 3)  # 随机延迟
            
            # 手动确认消息
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"ACK: {body}")
        except Exception as e:
            print(f"Failed: {body} - {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)





if __name__ == '__main__':
    OrderConsumer("xxx", "xxx", "xxx", "xxx", xxx, "/dev").run()