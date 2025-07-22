from email import message
from pydoc import text
import time
from urllib import response
from flask import Flask, request, jsonify
from dataclasses import dataclass
from typing import Dict,Optional,Any
import socket
import random
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread
import os
from scp.lab.client import SciLabClient
from scp.hub.permission import permission_server
import redis
from redis import ConnectionPool, Redis
from scp.hub.client_server import SSEClient
import base64

# headers = {
#     'Accept': 'text/event-stream',
#     'Cache-Control': 'no-cache',
#     'Connection': 'keep-alive'
# }
# sse_response = requests.get(
#     f"127.0.0.1:6100/sse",
#     headers=headers,
#     stream=True,
#     timeout=5
# )

app = Flask(__name__)


@dataclass
class Server:
    name: str
    description: str
    url: str
    port: int
    type: Optional[str] = None  # Optional type field for future use


# Global dictionaries to store servers and health status
servers: Dict[str, Server] = {}
health_cache: Dict[str, tuple[datetime, bool]] = {}

# Add constants for storage
# STORAGE_FILE = Path("servers.json")
STORAGE_FILE = Path(os.getenv("STORAGE_FILE_PATH", "servers.json"))


# Add constant for permission server name
PERMISSION_SERVER_NAME = "PermissionServer"


def _generate_port(
    server_url: str, start_port: int = 5000, end_port: int = 65535
) -> int:
    """Generate an available port for the server.

    Args:
        server_url: The server URL to check ports against
        start_port: Minimum port number to consider (default: 5000)
        end_port: Maximum port number to consider (default: 65535)

    Returns:
        An available port number
    """
    # Get host from server URL
    from urllib.parse import urlparse

    host = urlparse(server_url).hostname or "127.0.0.1"

    # Start with a random port in the range
    port = random.randint(start_port, end_port)

    while port <= end_port:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((host, port))
            sock.close()
            return port
        except socket.error:
            port += 1
        finally:
            sock.close()

    raise RuntimeError("No available ports found in the specified range")


def check_server_health(server: Server) -> bool:
    """Check if a server is healthy by pinging its health endpoint.
    Caches the result for 1 minutes.

    Args:
        server: Server instance to check

    Returns:
        bool: True if server is healthy, False otherwise
    """
    if server.type == "sse":
        return True  # Assume SSE servers are always healthy for now
    
    # Check if we have a recent cached result
    if server.name in health_cache:
        last_check, is_healthy = health_cache[server.name]
        if datetime.now() - last_check < timedelta(seconds=30):
            return is_healthy

    try:
        response = requests.get(f"{server.url}:{server.port}/health", timeout=5)
        is_healthy = response.status_code == 200
    except requests.RequestException:
        is_healthy = False

    health_cache[server.name] = (datetime.now(), is_healthy)
    return is_healthy


def load_servers() -> Dict[str, Server]:
    """Load servers from storage and verify they're running."""
    if not STORAGE_FILE.exists():
        return {}

    servers = {}
    try:
        with open(STORAGE_FILE, "r") as f:
            data = json.load(f)
            for server_data in data.values():
                server = Server(**server_data)
                if check_server_health(server):
                    servers[server.name] = server
                else:
                    print(f"Server {server.name} appears to be down, skipping...")
    except Exception as e:
        print(f"Error loading servers: {e}")

    return servers


def save_servers():
    """Save current servers to storage."""
    with open(STORAGE_FILE, "w") as f:
        json.dump({name: vars(server) for name, server in servers.items()}, f)


# 创建全局连接池
redis_pool = None

def create_redis_pool():
    """创建 Redis 连接池"""
    global redis_pool
    try:
        redis_pool = ConnectionPool(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            username=os.getenv("REDIS_USERNAME"),  # 添加用户名参数
            decode_responses=True,
            max_connections=10,  # 最大连接数
            socket_connect_timeout=5.0,
            socket_timeout=5.0
        )
        # 测试连接
        with Redis(connection_pool=redis_pool) as client:
            client.ping()
        print("Redis连接池初始化成功")
        return True
    except redis.ConnectionError as e:
        print(f"Redis连接池创建失败: {str(e)}")
        return False


def get_redis_client():
    """获取 Redis 客户端实例"""
    if redis_pool is None:
        if not create_redis_pool():
            return None
    return Redis(connection_pool=redis_pool)

# # 初始化连接池
create_redis_pool()


from typing import Dict, Any, Optional
from .aliyun_oss import AliyunOssStorage

def create_storage(storage_type: str, config: Dict[str, Any]) -> Any:
    """
    创建存储实例
    
    Args:
        storage_type: 存储类型 ('aliyun_oss', 等)
        config: 存储配置
        
    Returns:
        存储实例
    """
    if storage_type == 'aliyun_oss':
        return AliyunOssStorage(
            access_key_id=config.get('access_key_id'),
            access_key_secret=config.get('access_key_secret'),
            endpoint=config.get('endpoint'),
            bucket_name=config.get('bucket_name'),
            default_path_prefix=config.get('default_path_prefix', '')
        )
    else:
        raise ValueError(f"不支持的存储类型: {storage_type}")
    


@app.route("/get_server_result/<path:request_id>", methods=["GET"])
def get_redis_result(request_id: str) -> Optional[Dict[str, Any]]:
    """从Redis获取结果的处理函数"""
    try:
        redis_client = get_redis_client()
        if redis_client is None:
            return jsonify({"error": "Redis服务未就绪"}), 500

        with redis_client as client:
            result = client.get(f"{request_id}")
            
        if result is None:
            print(f"未找到请求ID: {request_id}的数据")
            return jsonify({"error": "数据不存在"}), 404

        return json.loads(result)

    except redis.RedisError as e:
        print(f"Redis操作失败: {str(e)}")
        return jsonify({"error": "Redis服务异常"}), 500
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {str(e)}")
        return jsonify({"error": "数据格式错误"}), 500


@app.route("/set_result/", methods=["POST"])
def set_redis_result() -> Dict[str, Any]:
    """设置或追加Redis结果的处理函数"""


    try:


    

        # 获取请求数据
        data = request.get_json()

        #是否包含文件上传
        files = None
        message = None
        text = None
        if isinstance(data, dict):
            result = data.get('result')
            if isinstance(result, dict):
                data_dict = result.get('data')
                if isinstance(data_dict, dict):
                    files = data_dict.get('files')
                    message = data_dict.get('message')
                    text = data_dict.get('text')

        new_file_path = []
        if files != None and len(files) > 0:
            for index, file in enumerate(files):
                base64bin = file.get("file")
                file_name = file.get("fileName")
                request_id = data.get("requestId")
                full_name = f"{request_id}_{index}_{file_name}"
                bin_data = base64.b64decode(base64bin)
                oss_config = {
            'access_key_id': os.environ.get('OSS_ACCESS_KEY_ID'),
            'access_key_secret': os.environ.get('OSS_ACCESS_KEY_SECRET'),
            'endpoint': os.environ.get('OSS_ENDPOINT', 'https://oss-cn-hangzhou.aliyuncs.com'),
            'bucket_name': os.environ.get('OSS_BUCKET_NAME'),
            'default_path_prefix': 'scp-data'
    }
                storage = create_storage('aliyun_oss', oss_config)

                if storage is None:
                    return jsonify({"error": "存储服务未就绪"}), 500    
                
                file_url = storage.upload_data(
                    data=bin_data,
                    remote_path=full_name
                )
                if file_url is None:
                    return jsonify({"error": "文件上传失败"}), 500
                
                new_file_path.append(file_url)
            
            #oos替换上传的文件路径
            data['result']['data']['files'] = new_file_path
        
        # 检查是否包含 requestId
            

        if not data or "requestId" not in data:
            return jsonify({"error": "缺少requestId"}), 400

        request_id = data["requestId"]
        redis_key = f"{request_id}"

        redis_client = get_redis_client()
        if redis_client is None:
            return jsonify({"error": "Redis服务未就绪"}), 500

        with redis_client as client:
            # 检查是否存在该key
            existing_data = client.get(redis_key)
            
            if existing_data:
                # 如果key存在，解析现有数据并追加新数据
                try:
                    existing_json = json.loads(existing_data)
                    if isinstance(existing_json, list):
                        existing_json.append(data)
                        new_data = existing_json
                    else:
                        new_data = [existing_json, data]
                except json.JSONDecodeError:
                    return jsonify({"error": "现有数据格式错误"}), 500
            else:
                # 如果key不存在，创建新的数据列表
                new_data = [data]

            # 设置数据，过期时间为1小时
            client.setex(redis_key, 3600, json.dumps(new_data))
            
            return jsonify({
                "message": "数据写入成功",
                "request_id": request_id
            })

    except redis.RedisError as e:
        print(f"Redis操作失败: {str(e)}")
        return jsonify({"error": "Redis服务异常"}), 500
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {str(e)}")
        return jsonify({"error": "数据格式错误"}), 500
    except Exception as e:
        print(f"未知错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500



#注册 sse、Streamable HTTP、scp-server
@app.route("/register_server", methods=["POST"])
def register_server():
    data = request.get_json()

     # Validate required fields
    required_fields = ["server_url", "server_name", "server_description"]

    type = data.get("type", "scp")  # Default to scp if not specified

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Block registration of permission server name by other servers
    if data["server_name"] == PERMISSION_SERVER_NAME:
        return jsonify({"error": "Reserved server name"}), 403

    port = -1
    
    if "server_port" in data and  data["server_port"] == -1:
        
        port = _generate_port(data["server_url"])
    else:
        port = data["server_port"]



    # Create new server instance
    new_server = Server(
        url=data["server_url"],
        name=data["server_name"],
        description=data["server_description"],
        port=port,
        type=type,  # Use provided type or default to "scp"
    )

    # Add to global dictionary
    servers[data["server_name"]] = new_server
    save_servers()  # Save after registration
    print("Added server: ", data["server_name"])

    return (
        jsonify(
            {
                "message": "Server registered successfully",
                "server": {
                    "name": new_server.name,
                    "url": new_server.url,
                    "description": new_server.description,
                    "port": new_server.port,
                    "type": new_server.type 
                },
            }
        ),
        201,
    )


@app.route("/servers", methods=["GET"])
def get_servers():
    """Return a list of all registered and healthy servers."""
    return jsonify(
        [
            {
                "name": server.name,
                "url": server.url,
                "description": server.description,
                "port": server.port,
            }
            for server in servers.values()
            if check_server_health(server)
        ]
    )


@app.route("/tools", methods=["GET"])
def get_tools():
    """Return a list of tools from registered servers."""
    server_name = request.args.get("server_name")

    all_tools = []
    try:
        # Filter servers if server_name is provided
        target_servers = [servers[server_name]] if server_name else servers.values()
        for server in target_servers:

            if server.type == "scp":
                try:
                    if not check_server_health(server):
                        continue
                    client = SciLabClient(f"{server.url}:{server.port}")
                    for tool in client.list_tools():
                        tool.name = f"{server.name}.{tool.name}"
                        all_tools.append(tool)
                except Exception as e:
                    print(f"Error fetching tools from {server.name}: {e}")
                    health_cache[server.name] = (datetime.now(), False)
                    continue
            elif server.type == "sse":
                try:
                    import asyncio
                    # 创建一个异步函数来处理所有异步操作
                    async def fetch_sse_tools():
                        async with SSEClient(f"{server.url}:{server.port}/sse") as client:
                            return await client.list_tools()
                    
                    # 在同步代码中正确使用asyncio.run()来执行异步函数
                    results = asyncio.run(fetch_sse_tools())
                    for tool in results.tools:
                        tool.name = f"{server.name}.{tool.name}"
                        all_tools.append(tool)
                except Exception as e:
                    print(f"Error fetching tools from {server.name}: {e}")
                    health_cache[server.name] = (datetime.now(), False)
                    continue
            
        return json.dumps([tool.model_dump() for tool in all_tools])
    except KeyError:
        return jsonify({"error": f"Server '{server_name}' not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tools/call_tool", methods=["POST"])
def call_tool():
    """Call a tool on a specific server."""
    data = request.get_json()
    name = data.pop("name", None)  # Extract and remove name from arguments

    if name is None:
        return jsonify({"error": "Tool name not provided"}), 400

    server_name = None
    tool_name = name

    # Check if server name is specified (format: "server_name.tool_name")
    if "." in tool_name:
        server_name, tool_name = tool_name.split(".", 1)

        # Add permission server tool restriction
        if tool_name == "ask_for_permission" and server_name != PERMISSION_SERVER_NAME:
            return jsonify({"error": "Permission denied: unauthorized server"}), 403

        if server_name not in servers:
            return jsonify({"error": f"Server '{server_name}' not found"}), 404
        target_servers = [servers[server_name]]
    else:
        # If no server specified, search all servers for the tool
        if tool_name == "ask_for_permission":
            target_servers = [servers[PERMISSION_SERVER_NAME]]
        else:
            target_servers = [s for s in servers.values() if check_server_health(s)]

    # Try each potential server
    for server in target_servers:


        if server.type == "sse":
            import asyncio
            try:
                # 创建一个异步函数来处理所有异步操作
                async def fetch_sse_toolcall():
                    async with SSEClient(f"{server.url}:{server.port}/sse") as client:
                        # 在同步代码中正确使用asyncio.run()来执行异步函数
                        response = await client.call_tool(tool_name, data)
                    return response.content
                
                result = asyncio.run(fetch_sse_toolcall())
                return jsonify([content.model_dump() for content in result])

                    
            except requests.RequestException:
                # If this server fails, try the next one
                continue
        
        elif server.type == "scp":

            try:
                client = SciLabClient(f"{server.url}:{server.port}")
                # Check if the tool exists on this server
                available_tools = client.list_tools()
                print("AVAILABLE TOOLS", available_tools)
                if not any(t.name == tool_name for t in available_tools):
                    continue

                # Found the tool, try to call it
                result = client.call_tool(
                    tool_name, data
                )  # Use remaining data as arguments
                return jsonify([content.model_dump() for content in result])
            
            except requests.RequestException:
                # If this server fails, try the next one
                continue



        # If we get here, we didn't find the tool on any server
        error_msg = f"Tool '{tool_name}' not found"
        if server_name:
            error_msg += f" on server '{server_name}'"
        print("ERROR", error_msg)
        return jsonify({"error": error_msg}), 404


def load_permission_server():
    permission_server_url = "http://127.0.0.1"
    permission_port = _generate_port(permission_server_url)

    permission_server_instance = Server(
        name=PERMISSION_SERVER_NAME,
        description=permission_server.mcp.description,  # type: ignore
        url=permission_server_url,
        port=permission_port,
        type="scp"
    )

    # Add to global servers dict
    servers[PERMISSION_SERVER_NAME] = permission_server_instance

    # Start permission server in a new thread with the assigned port
    permission_thread = Thread(
        target=lambda: permission_server.mcp.run_http(
            register_server=False, port=permission_port
        ),
        daemon=True,
    )
    permission_thread.start()
    time.sleep(1)


def init_app():
    # Register permission server first
    load_permission_server()
    # Load other servers on startup
    loaded_servers = load_servers()
    for server in loaded_servers.keys():
        if server != PERMISSION_SERVER_NAME:
            servers[server] = loaded_servers[server]
            print(f"Loaded server: {server}")
    save_servers()

# 在模块加载时自动初始化（无论是gunicorn还是python直接运行）
init_app()

def run(host: str = "0.0.0.0", port: int = 46380):
    print(f"Starting server on {host}:{port}")
    app.run(
        host=host,
        port=port,
        debug=False
    )
