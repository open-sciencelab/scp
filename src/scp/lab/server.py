from scp.server.fastmcp import FastMCP
from flask import Flask, request, Response
from typing import Any, Optional
import json
import requests


class SciLabServer(FastMCP):
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **settings: Any,
    ):
        super().__init__(name=name, **settings)
        self.description = description
        self.flask_app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.flask_app.route("/tools", methods=["GET"])
        async def list_tools():
            tools = await self.list_tools()
            return json.dumps([tool.model_dump() for tool in tools])

        @self.flask_app.route("/tools/call_tool", methods=["POST"])
        async def call_tool():
            arguments = request.get_json()
            name = arguments.pop("name", None)
            if name is None:
                return json.dumps({"error": "Tool name not provided"}), 400
            result = await self.call_tool(name, arguments)
            return json.dumps([content.model_dump() for content in result])

        @self.flask_app.route("/resources", methods=["GET"])
        async def list_resources():
            resources = await self.list_resources()
            # Convert resources to a list of dictionaries that can be JSON serialized
            resource_list = []
            for resource in resources:
                try:
                    resource_dict = resource.model_dump()
                    # Ensure all values are JSON serializable
                    for key, value in resource_dict.items():
                        if not isinstance(
                            value, (str, int, float, bool, type(None), list, dict)
                        ):
                            resource_dict[key] = str(value)
                    resource_list.append(resource_dict)
                except Exception as e:
                    # Handle any serialization errors
                    resource_list.append(
                        {"error": f"Failed to serialize resource: {str(e)}"}
                    )
            return json.dumps(resource_list)

        @self.flask_app.route("/resources/<path:uri>", methods=["GET"])
        async def read_resource(uri: str):
            content = await self.read_resource(uri)
            return Response(content)

        @self.flask_app.route("/prompts", methods=["GET"])
        async def list_prompts():
            prompts = await self.list_prompts()
            return json.dumps([prompt.model_dump() for prompt in prompts])

        @self.flask_app.route("/prompts/<name>", methods=["POST"])
        async def get_prompt(name: str):
            arguments = request.get_json()
            result = await self.get_prompt(name, arguments)
            return json.dumps(result.model_dump())

        @self.flask_app.route("/health", methods=["GET"])
        async def health_check():
            return json.dumps(
                {
                    "status": "healthy",
                    "server_name": self.name,
                    "description": self.description,
                }
            )

    def register_server(
        self,
        server_url: str = "121.5.254.174",
        server_port: int = -1,
        registry_url: str = "121.5.254.174:46380",
    ) -> int:
        """Register the server with the registry. Returns the port to use for the server.

        Args:
            server_url: URL of the server to register.
            registry_url: URL of the registry to register with.
        """
        server_data = {
            "server_url": f"http://{server_url}",
            "server_name": self.name or "unnamed_server",
            "server_description": self.description or "SCP Server",
            "server_port":server_port,
            "type":"scp"
        }

        try:
            response = requests.post(
                f"http://{registry_url}/register_server",
                json=server_data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            print(f"Successfully registered server with registry at {registry_url}")
            return response.json()["server"]["port"]
        except requests.exceptions.RequestException as e:
            print(f"Failed to register server: {str(e)}")
            return 0

    def run_http(
        self,
        host: str = "0.0.0.0",
        register_server: bool = True,
        port: int = -1,
        registry_url:str = "0.0.0.0:5000",
    ) -> None:
        """Run the HTTP server.

        Args:
            host: Host to bind to (default: "0.0.0.0")
            port: Port to listen on (default: 5000)
            register_server: Whether to register the server with the registry (default: True)
        """
        if register_server:
            port = self.register_server(server_url=host,server_port= port,registry_url=registry_url)
        self.flask_app.run(host="0.0.0.0", port=port)
