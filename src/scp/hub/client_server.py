# mcp_client_demo.py
import asyncio
from scp.client.session import ClientSession
from scp.client.sse import sse_client
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SSEClient:
    def __init__(self, server_url="http://101.126.156.90:56680/sse"):
        #     def __init__(self, server_url="http://127.0.0.1:1234/sse"):

        self.server_url = server_url
        self._sse_context = None
        self._session = None

    async def __aenter__(self):
        # 创建 SSE 通道
        self._sse_context = sse_client(self.server_url)
        self.read, self.write = await self._sse_context.__aenter__()

        # 创建 SCP 会话
        self._session = ClientSession(self.read, self.write)
        await self._session.__aenter__()
        await self._session.initialize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
        if self._sse_context:
            await self._sse_context.__aexit__(exc_type, exc_val, exc_tb)

    async def list_tools(self):
        return await self._session.list_tools()

    async def list_resources(self):
        return await self._session.list_resources()

    async def call_tool(self, name, arguments):
        try:
            return await asyncio.wait_for(
                self._session.call_tool(name, arguments),
                timeout=30.0  # 30秒超时
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"调用工具 {name} 超时")