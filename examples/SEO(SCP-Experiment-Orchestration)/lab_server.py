from scp.lab.server import SciLabServer

from scp.lab.lab_operator.base import register_scp_tools
from scp.lab.cloud.cloud_devices import get_device_cloud_instance
from lab import Lab_Devices
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

 
lab_device = Lab_Devices()

# Get Device cloud instance
cloud_device = get_device_cloud_instance("admin","louwenjie","git-demo", "127.0.0.1", 5672, "/", "http://127.0.0.1:8081")

# Create edge-server
git_demo = SciLabServer("git-demo", description="A Server that runs Huixiang Lab")

register_scp_tools(git_demo, lab_device)


if __name__ == "__main__":

        git_demo.run_http(host="127.0.0.1",port=18081,registry_url= "127.0.0.1:8081" )

