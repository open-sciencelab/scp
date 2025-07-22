"""

specific parameter and result types.
"""
from operator import index
import stat
import time
from typing import Dict, TypedDict, Any, Optional, Type,List
from scp.lab.lab_operator import BaseParams,DeviceParams,StatusMessage,DeviceStatus,ActionResult
from scp.lab.lab_operator import BaseOperator,device_action,agent_action,scp_register
from    scp.lab.cloud.base_operator import publish_message,create_status_message
import os 
import requests
import random
import json
registry_url = os.getenv("registry_url")



class Lab_Parms_Fluorescence_Intensity_Measurement:
    """荧光强度测定"""    
    sample_id: str
        # sample_id: list[str]

class Lab_Parms_Compute_Protein_Parameters:
    """荧光强度测定"""    
    protein: str
        # sample_id: list[str]


class Lab_Parms_Plan_Start:
    """蛋白质检索"""    
    experiment_code: str
    experiment_name: str # type: ignore
    loop_count: int

class Lab_Parms_Protein_Determination:
    """蛋白质纯化预测"""    
    sample_id: str
        # sample_id: list[str]



class Lab_Parms_Protein_Purification:
    """蛋白质纯化预测"""    
    sample_id: str
          # sample_id: list[str]



class Lab_Parms_Protein_Mutation_Prediction:
    """蛋白质突变预测"""    
    pdb_path: str     
    protein_seq: str


class Lab_Parms_Protein_Research:
    """蛋白质检索"""    
    UniProt_ID: str

class Lab_Parms_Protein_Fold:
    """蛋白质折叠"""    
    fasta_path: str

class Lab_Parms_Protein_Visual:
    """蛋白质可视化"""    
    pdb_path: str
    mode:str
    rotate:str



class Lab_Predict_Secondary_Structure:
    """二级结构预测"""
    sequence: str


class Lab_Compute_PI_mW:
    """计算等电点"""
    protein: str


class Lab_Assign_Stereochemistry:
    """分配立体化学"""
    smiles: str


class Lab_Get_Formal_Charge_of_Atoms:
    """获取原子的形式电荷"""
    smiles: str



class Lab_List_Functional_Groups:
    """获取功能组列表"""
    smiles: str



class Lab_compute_pI_mW:
    """计算蛋白质序列的理论等电点（pI）和分子量（mW）。"""
    protein: str


class Lab_compute_protein_parameters:
    """计算蛋白质参数"""
    protein: str


class Lab_predict_hydrophilicity:
    """预测亲水性"""
    protein: str


class Lab_compute_extinction_coefficient:
    """计算消光系数"""
    protein: str


class Lab_predict_signalpeptide:
    """预测信号肽"""
    protein: str


class Lab_Devices(BaseOperator):
    """Tescan device implementation."""
    lab_name = "huixiang_lab"
    device_name = "huixiang_lab_device"

    def __init__(self):
        self._param_classes: Dict[str, Type[DeviceParams]] = {}
        
        # 初始化时动态创建所有工具方法
        # self._initialize_tools()
        super().__init__()

    @scp_register("predict_signalpeptide")
    @device_action("predict_signalpeptide")
    def predict_signalpeptide(self, params:Lab_predict_signalpeptide):
        """预测信号肽"""

        try:
            # Internal OS Experiment Orchestration System
            url = "http://115.190.155.83/api/model/services/6870c61c096f646b958e806d/app/api/predict_signalpeptide"



            headers = {
                "Authorization": "Bearer  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdPaWQiOiI2ODJiZmRmMjNmMTUxNWE1Zjg4YTg1NjEiLCJ1c2VyT2lkIjoiNjg1NGUzMjQ3ZmY5Nzg4YjcwMWFjMjZlIiwibmFtZSI6Imx3aiIsImlzT3BlbkFQSSI6dHJ1ZSwiYXBwIjoiTW9kZWxTZXJ2aWNlIiwiYXBwSWQiOiI2ODRhZWExODI2ODQzOTViOTU3Y2ZkNTkiLCJpYXQiOjE3NTA3NjY0NDMsImlzcyI6Imh0dHA6Ly84LjE0NS4zMy4xMCJ9.1Pq-RNl1uIl7XjgEv3GwF3UGjd26_RZ9sV-XFKCeq5c"
}



            payload = {

                "protein": str(params.get("protein")),  # 从参数中获取sequence


            }

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                return ActionResult(
                            message="预测信号肽成功",
                            messageStatus=1,  # Assuming 2 indicates success
                            result = response.json(),
                            index=0                 
                        )
                
            else:
                return ActionResult(
                    message="预测信号肽失败",
                    messageStatus=-1,  # Assuming 2 indicates success
                    index=0
                )
            
        
        except Exception as e:
            return ActionResult(
                message=f"预测信号肽异常: {str(e)}",
                messageStatus=-1,  # Assuming 2 indicates success
                index=0
            )
        




    @scp_register("compute_extinction_coefficient")
    @device_action("compute_extinction_coefficient")
    def compute_extinction_coefficient(self, params:Lab_compute_extinction_coefficient):
        """计算消光系数"""

        try:
            # Internal OS Experiment Orchestration System
            url = "http://115.190.155.83/api/model/services/6870c61c096f646b958e806d/app/api/compute_extinction_coefficient"



            headers = {
                "Authorization": "Bearer  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdPaWQiOiI2ODJiZmRmMjNmMTUxNWE1Zjg4YTg1NjEiLCJ1c2VyT2lkIjoiNjg1NGUzMjQ3ZmY5Nzg4YjcwMWFjMjZlIiwibmFtZSI6Imx3aiIsImlzT3BlbkFQSSI6dHJ1ZSwiYXBwIjoiTW9kZWxTZXJ2aWNlIiwiYXBwSWQiOiI2ODRhZWExODI2ODQzOTViOTU3Y2ZkNTkiLCJpYXQiOjE3NTA3NjY0NDMsImlzcyI6Imh0dHA6Ly84LjE0NS4zMy4xMCJ9.1Pq-RNl1uIl7XjgEv3GwF3UGjd26_RZ9sV-XFKCeq5c"
}



            payload = {

                "protein": str(params.get("protein")),  # 从参数中获取sequence


            }

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                return ActionResult(
                            message="计算消光系数成功",
                            messageStatus=1,  # Assuming 2 indicates success
                            result = response.json(),
                            index=0                 
                        )
                
            else:
                return ActionResult(
                    message="计算消光系数失败",
                    messageStatus=-1,  # Assuming 2 indicates success
                    index=0
                )
            
        
        except Exception as e:
            return ActionResult(
                message=f"计算消光系数异常: {str(e)}",
                messageStatus=-1,  # Assuming 2 indicates success
                index=0
            )
        


    @scp_register("predict_hydrophilicity")
    @device_action("predict_hydrophilicity")
    def predict_hydrophilicity(self, params:Lab_predict_hydrophilicity):
        """预测亲水性"""

        try:
            # Internal OS Experiment Orchestration System
            url = "http://115.190.155.83/api/model/services/6870c61c096f646b958e806d/app/api/predict_hydrophilicity"

            headers = {
                "Authorization": "Bearer  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdPaWQiOiI2ODJiZmRmMjNmMTUxNWE1Zjg4YTg1NjEiLCJ1c2VyT2lkIjoiNjg1NGUzMjQ3ZmY5Nzg4YjcwMWFjMjZlIiwibmFtZSI6Imx3aiIsImlzT3BlbkFQSSI6dHJ1ZSwiYXBwIjoiTW9kZWxTZXJ2aWNlIiwiYXBwSWQiOiI2ODRhZWExODI2ODQzOTViOTU3Y2ZkNTkiLCJpYXQiOjE3NTA3NjY0NDMsImlzcyI6Imh0dHA6Ly84LjE0NS4zMy4xMCJ9.1Pq-RNl1uIl7XjgEv3GwF3UGjd26_RZ9sV-XFKCeq5c"
}



            payload = {

                "protein": str(params.get("protein")),  # 从参数中获取sequence


            }

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                return ActionResult(
                            message="预测亲水性成功",
                            messageStatus=1,  # Assuming 2 indicates success
                            result = response.json(),
                            index=0                 
                        )
                
            else:
                return ActionResult(
                    message="预测亲水性失败",
                    messageStatus=-1,  # Assuming 2 indicates success
                    index=0
                )
            
        
        except Exception as e:
            return ActionResult(
                message=f"预测亲水性异常: {str(e)}",
                messageStatus=-1,  # Assuming 2 indicates success
                index=0
            )
        


    
    @scp_register("compute_protein_parameters")
    @device_action("compute_protein_parameters")
    def compute_protein_parameters(self, params:Lab_compute_protein_parameters):
        """计算蛋白质参数"""

        try:

            # Internal OS Experiment Orchestration System
            url = "http://115.190.155.83/api/model/services/6870c61c096f646b958e806d/app/api/compute_protein_parameters"



            headers = {
                "Authorization": "Bearer  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdPaWQiOiI2ODJiZmRmMjNmMTUxNWE1Zjg4YTg1NjEiLCJ1c2VyT2lkIjoiNjg1NGUzMjQ3ZmY5Nzg4YjcwMWFjMjZlIiwibmFtZSI6Imx3aiIsImlzT3BlbkFQSSI6dHJ1ZSwiYXBwIjoiTW9kZWxTZXJ2aWNlIiwiYXBwSWQiOiI2ODRhZWExODI2ODQzOTViOTU3Y2ZkNTkiLCJpYXQiOjE3NTA3NjY0NDMsImlzcyI6Imh0dHA6Ly84LjE0NS4zMy4xMCJ9.1Pq-RNl1uIl7XjgEv3GwF3UGjd26_RZ9sV-XFKCeq5c"
}



            payload = {

                "protein": str(params.get("protein")),  # 从参数中获取sequence


            }

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                return ActionResult(
                            message="计算蛋白质参数成功",
                            messageStatus=1,  # Assuming 2 indicates success
                            result = response.json(),
                            index=0                 
                        )
                
            else:
                return ActionResult(
                    message="计算蛋白质参数失败",
                    messageStatus=-1,  # Assuming 2 indicates success
                    index=0
                )
            
        
        except Exception as e:
            return ActionResult(
                message=f"计算蛋白质参数异常: {str(e)}",
                messageStatus=-1,  # Assuming 2 indicates success
                index=0
            )





    @scp_register("compute_pI_mW")
    @device_action("compute_pI_mW")
    def compute_pI_mW(self, params:Lab_compute_pI_mW):
        """计算蛋白质序列的理论等电点（pI）和分子量（mW）。"""


        try:
            # Internal OS Experiment Orchestration System
            url = "http://115.190.155.83/api/model/services/6870c61c096f646b958e806d/app/api/compute_pI_mW"



            headers = {
                "Authorization": "Bearer  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdPaWQiOiI2ODJiZmRmMjNmMTUxNWE1Zjg4YTg1NjEiLCJ1c2VyT2lkIjoiNjg1NGUzMjQ3ZmY5Nzg4YjcwMWFjMjZlIiwibmFtZSI6Imx3aiIsImlzT3BlbkFQSSI6dHJ1ZSwiYXBwIjoiTW9kZWxTZXJ2aWNlIiwiYXBwSWQiOiI2ODRhZWExODI2ODQzOTViOTU3Y2ZkNTkiLCJpYXQiOjE3NTA3NjY0NDMsImlzcyI6Imh0dHA6Ly84LjE0NS4zMy4xMCJ9.1Pq-RNl1uIl7XjgEv3GwF3UGjd26_RZ9sV-XFKCeq5c"
}



            payload = {

                "protein": str(params.get("protein")),  # 从参数中获取sequence


            }

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                return ActionResult(
                            message="计算蛋白质序列的理论等电点（pI）和分子量（mW）成功",
                            messageStatus=1,  # Assuming 2 indicates success
                            result = response.json(),
                            index=0                 
                        )
                
            else:
                return ActionResult(
                    message="计算蛋白质序列的理论等电点（pI）和分子量（mW）失败",
                    messageStatus=-1,  # Assuming 2 indicates success
                    index=0
                )
            
        
        except Exception as e:
            return ActionResult(
                message=f"计算蛋白质序列的理论等电点（pI）和分子量（mW）异常: {str(e)}",
                messageStatus=-1,  # Assuming 2 indicates success
                index=0
            )


