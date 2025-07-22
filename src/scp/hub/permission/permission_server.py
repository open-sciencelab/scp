"""
FastMCP Permission Server
Handles permission requests through dialog boxes
"""

import logging
import tempfile
import os
import sys
import subprocess
import time
from scp.lab.server import SciLabServer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create server
mcp = SciLabServer(
    "PermissionServer", description="A Server that handles permission requests"
)


@mcp.tool()
def ask_for_permission(description: str) -> bool:
    """
    Display a permission request dialog and return the user's choice

    Args:
        description: The permission request description to show to the user

    Returns:
        bool: True if permission granted, False if denied
    """
    with tempfile.NamedTemporaryFile(mode="w+t", delete=False) as temp_file:
        temp_file_name = temp_file.name
        temp_file.write(description)
        temp_file.flush()

    try:
        dialog_script = os.path.join(
            os.path.dirname(__file__), "qt_permission_dialog.py"
        )
        result = subprocess.call([sys.executable, dialog_script, temp_file_name])
        return result == 0
    finally:
        os.remove(temp_file_name)


def start_server_delayed():
    time.sleep(5)
    mcp.run_http()


if __name__ == "__main__":
    print(ask_for_permission("Do you want to allow this?"))
