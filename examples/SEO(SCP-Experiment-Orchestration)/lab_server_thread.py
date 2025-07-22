
from lab import Lab_Devices
from scp.lab.cloud.cloud_consumer import OrderConsumer
lab_Devices = Lab_Devices()

# Create OrderConsumer instance
orderConsumer = OrderConsumer("git-demo", "admin", "louwenjie", "127.0.0.1", 5672, "/","http://127.0.0.1:8081",lab_Devices)

# Run device twin
try:
    orderConsumer.run()
except KeyboardInterrupt:
    print("\nShutting down lab environment...")

