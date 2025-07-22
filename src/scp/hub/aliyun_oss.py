"""
阿里云 OSS 存储模块，提供文件上传、下载和管理功能。
"""
import os
import oss2
import logging
from typing import Optional, Dict, List, BinaryIO, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class AliyunOssStorage:
    """阿里云 OSS 存储类，提供文件上传下载等操作"""
    
    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        bucket_name: str,
        default_path_prefix: str = ""
    ):
        """
        初始化阿里云 OSS 存储
        
        Args:
            access_key_id: 阿里云访问密钥ID
            access_key_secret: 阿里云访问密钥密码
            endpoint: OSS服务区域节点（如：http://oss-cn-hangzhou.aliyuncs.com）
            bucket_name: 存储桶名称
            default_path_prefix: 默认存储路径前缀
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        self.default_path_prefix = default_path_prefix
        
        # 创建认证对象
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        # 创建存储桶对象
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
        
        logger.info(f"已初始化阿里云OSS存储: bucket={bucket_name}, endpoint={endpoint}")
    
    def upload_file(
        self, 
        local_file_path: Union[str, Path], 
        remote_path: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        上传文件到OSS
        
        Args:
            local_file_path: 本地文件路径
            remote_path: 远程存储路径，不指定则使用本地文件名
            metadata: 元数据字典
            
        Returns:
            上传后的OSS文件URL
        """
        local_file_path = Path(local_file_path)
        
        # 如果未指定远程路径，使用本地文件名
        if not remote_path:
            remote_path = local_file_path.name
        
        # 添加路径前缀
        if self.default_path_prefix and not remote_path.startswith(self.default_path_prefix):
            remote_path = f"{self.default_path_prefix.rstrip('/')}/{remote_path}"
        
        # 上传文件
        try:
            if metadata:
                headers = {'x-oss-meta-' + k: v for k, v in metadata.items()}
                self.bucket.put_object_from_file(remote_path, str(local_file_path), headers=headers)
            else:
                self.bucket.put_object_from_file(remote_path, str(local_file_path))
                
            logger.info(f"文件上传成功: {local_file_path} -> {remote_path}")
            
            # 构造文件URL
            file_url = f"https://{self.bucket_name}.{self.endpoint.replace('http://', '')}/{remote_path}"
            return file_url
            
        except oss2.exceptions.OssError as e:
            logger.error(f"上传文件失败: {str(e)}")
            raise
    
    def upload_data(
        self,
        data: Union[bytes, str, BinaryIO],
        remote_path: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        上传数据到OSS
        
        Args:
            data: 要上传的数据（字节、字符串或文件对象）
            remote_path: 远程存储路径
            metadata: 元数据字典
            
        Returns:
            上传后的OSS文件URL
        """
        # 添加路径前缀
        if self.default_path_prefix and not remote_path.startswith(self.default_path_prefix):
            remote_path = f"{self.default_path_prefix.rstrip('/')}/{remote_path}"
        
        # 处理不同类型的数据
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # 上传数据
        try:
            if metadata:
                headers = {'x-oss-meta-' + k: v for k, v in metadata.items()}
                self.bucket.put_object(remote_path, data, headers=headers)
            else:
                self.bucket.put_object(remote_path, data)
                
            logger.info(f"数据上传成功: {remote_path}")
            
            # 构造文件URL
            file_url = f"https://{self.bucket_name}.{self.endpoint.replace('https://', '')}/{remote_path}"
            return file_url
            
        except oss2.exceptions.OssError as e:
            logger.error(f"上传数据失败: {str(e)}")
            raise
    
    def download_file(
        self, 
        remote_path: str, 
        local_file_path: Union[str, Path]
    ) -> Path:
        """
        从OSS下载文件
        
        Args:
            remote_path: OSS中的文件路径
            local_file_path: 保存到本地的路径
            
        Returns:
            本地文件路径
        """
        local_file_path = Path(local_file_path)
        
        # 添加路径前缀
        if self.default_path_prefix and not remote_path.startswith(self.default_path_prefix):
            remote_path = f"{self.default_path_prefix.rstrip('/')}/{remote_path}"
        
        # 确保本地目录存在
        os.makedirs(local_file_path.parent, exist_ok=True)
        
        try:
            # 下载文件
            self.bucket.get_object_to_file(remote_path, str(local_file_path))
            logger.info(f"文件下载成功: {remote_path} -> {local_file_path}")
            return local_file_path
            
        except oss2.exceptions.OssError as e:
            logger.error(f"下载文件失败: {str(e)}")
            raise
    
    def download_data(self, remote_path: str) -> bytes:
        """
        从OSS下载数据
        
        Args:
            remote_path: OSS中的文件路径
            
        Returns:
            文件内容的字节数据
        """
        # 添加路径前缀
        if self.default_path_prefix and not remote_path.startswith(self.default_path_prefix):
            remote_path = f"{self.default_path_prefix.rstrip('/')}/{remote_path}"
        
        try:
            # 下载数据
            object_stream = self.bucket.get_object(remote_path)
            data = object_stream.read()
            logger.info(f"数据下载成功: {remote_path}")
            return data
            
        except oss2.exceptions.OssError as e:
            logger.error(f"下载数据失败: {str(e)}")
            raise
    
    def list_files(self, prefix: str = "", delimiter: str = "") -> List[str]:
        """
        列出指定前缀的文件
        
        Args:
            prefix: 路径前缀
            delimiter: 分隔符，用于分组结果
            
        Returns:
            文件名列表
        """
        # 添加路径前缀
        if self.default_path_prefix and prefix:
            prefix = f"{self.default_path_prefix.rstrip('/')}/{prefix}"
        elif self.default_path_prefix:
            prefix = self.default_path_prefix
        
        files = []
        for obj in oss2.ObjectIterator(self.bucket, prefix=prefix, delimiter=delimiter):
            if obj.is_prefix():  # 文件夹
                files.append(f"{obj.key}")
            else:  # 文件
                files.append(obj.key)
                
        return files
    
    def delete_file(self, remote_path: str) -> bool:
        """
        删除OSS中的文件
        
        Args:
            remote_path: OSS中的文件路径
            
        Returns:
            是否删除成功
        """
        # 添加路径前缀
        if self.default_path_prefix and not remote_path.startswith(self.default_path_prefix):
            remote_path = f"{self.default_path_prefix.rstrip('/')}/{remote_path}"
        
        try:
            self.bucket.delete_object(remote_path)
            logger.info(f"文件删除成功: {remote_path}")
            return True
            
        except oss2.exceptions.OssError as e:
            logger.error(f"删除文件失败: {str(e)}")
            return False
    
    def get_file_metadata(self, remote_path: str) -> Dict[str, str]:
        """
        获取文件元数据
        
        Args:
            remote_path: OSS中的文件路径
            
        Returns:
            元数据字典
        """
        # 添加路径前缀
        if self.default_path_prefix and not remote_path.startswith(self.default_path_prefix):
            remote_path = f"{self.default_path_prefix.rstrip('/')}/{remote_path}"
        
        try:
            header = self.bucket.get_object_meta(remote_path)
            metadata = {}
            
            # 提取自定义元数据
            for k, v in header.items():
                if k.startswith('x-oss-meta-'):
                    metadata[k[11:]] = v
                    
            return metadata
            
        except oss2.exceptions.OssError as e:
            logger.error(f"获取元数据失败: {str(e)}")
            raise
    
    def generate_presigned_url(
        self, 
        remote_path: str, 
        expires: int = 3600, 
        method: str = 'GET'
    ) -> str:
        """
        生成预签名URL，用于临时访问
        
        Args:
            remote_path: OSS中的文件路径
            expires: 过期时间（秒）
            method: 请求方法（GET/PUT）
            
        Returns:
            预签名URL
        """
        # 添加路径前缀
        if self.default_path_prefix and not remote_path.startswith(self.default_path_prefix):
            remote_path = f"{self.default_path_prefix.rstrip('/')}/{remote_path}"
        
        try:
            method_map = {
                'GET': oss2.OBJECT_GET,
                'PUT': oss2.OBJECT_PUT
            }
            
            url = self.bucket.sign_url(method_map.get(method, oss2.OBJECT_GET), 
                                        remote_path, 
                                        expires)
            logger.info(f"生成预签名URL: {remote_path}, 过期时间: {expires}秒")
            return url
            
        except oss2.exceptions.OssError as e:
            logger.error(f"生成预签名URL失败: {str(e)}")
            raise