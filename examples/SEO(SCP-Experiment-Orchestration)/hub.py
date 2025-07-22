
import os

os.environ["REDIS_HOST"] = "127.0.0.1"
os.environ["REDIS_PORT"] = "6379"
os.environ["REDIS_USERNAME"] = "default"
os.environ["REDIS_PASSWORD"] = "123456"
os.environ["REDIS_DB"] = "0"



os.environ["OSS_ACCESS_KEY_ID"] = "xxx"
os.environ["OSS_ACCESS_KEY_SECRET"] = "xxxx"
os.environ["OSS_ENDPOINT"] = "xxxx"
os.environ["OSS_BUCKET_NAME"] = "xxxx"

from scp.hub import hub_server

if __name__ == "__main__":
    hub_server.run(port=8081)


