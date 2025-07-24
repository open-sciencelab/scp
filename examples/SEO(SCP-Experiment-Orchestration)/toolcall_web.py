import asyncio
import json
import httpx
import gradio as gr
import sys
import os
import socket
from scp.lab.client import SciLabClient
from pathlib import Path
from openai import OpenAI
llm_client = OpenAI(api_key="sk-xxx", base_url="https://api.deepseek.com")
# Create client
client = SciLabClient("http://127.0.0.1:8081")

tools = client.list_tools()

all_tools = []
for tool in tools:
    parameters = tool.inputSchema or {}
    if not parameters.get("type"):
        parameters = {
            "type": "object",
            "properties": parameters,
            "required": list(parameters.keys())
        }
    all_tools.append({
        "type": "function",
        "function": {
            "name": tool.name.replace('.', '--'),  # 替换点号为右方括号
            "description": tool.description,
            "parameters": parameters
        }
    })



# 设置导入路径
current_dir = Path(__file__).parent  # demo目录
parent_dir = current_dir.parent  # scp目录

# 首先清理可能重复的路径
if str(parent_dir) in sys.path:
    sys.path.remove(str(parent_dir))

# 添加scp-client目录到路径
sys.path.append(str(parent_dir))

# 检测运行环境
def is_running_in_docker():
    """检查是否在Docker容器中运行"""
    path = '/proc/self/cgroup'
    return os.path.exists('/.dockerenv') or (os.path.isfile(path) and any('docker' in line for line in open(path)))

# 获取服务主机名和端口
DOCKER_ENV = is_running_in_docker()


# 适配不同环境的服务URL
def adapt_service_url(url):
    """根据当前环境适配服务URL
    注意：此函数用于自定义注册时的URL适配，不会修改scp.json中的URL
    """

    return url


def process_query_stream(query, all_tools, client, history=None):
    messages = [
        {"role": "system", "content": "你是一个智能助手，根据需要可以调用工具来帮助用户回答问题。"},
        {"role": "user", "content": query}
    ]
    if history is None:
        history = []


    while True:
        response = llm_client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=all_tools
        )
        content = response.choices[0]
        messages.append(content.message)
        if content.finish_reason == "tool_calls":
            tool_calls = content.message.tool_calls
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                try:
                    result = client.call_tool(function_name.replace('--', '.'), function_args)
                    message = result[0].text
                    result_str = message
                except Exception as e:
                    result_str = function_name + " 执行失败: " + str(e)
                # 追加中间结果到history并yield
                history = history + [(f"[工具调用] {function_name}", result_str)]
                yield history
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": result_str,
                })
        else:
            # yield最终回复
            history = history + [(query, content.message.content.strip())]
            yield history
            break


async def query_mcp_service(query_text):
        

    return process_query_stream(query_text, all_tools, client)


    

def add_user_message(query, history):
    """将用户消息添加到历史记录中"""
    if not query.strip():
        return "", history
    
    history = history or []
    # 只添加用户消息，不添加响应
    history.append((query, None))
    return "", history

def get_bot_response(history):
    if not history or history[-1][1] is not None:
        return history
    user_message = history[-1][0]
    # 获取响应和中间history
    response, new_history = process_query_sync(user_message, all_tools, client, history)
    # 更新历史记录的最后一项，添加最终响应
    new_history.append((user_message, response))
    return new_history

def get_bot_response_stream(history):
    if not history or history[-1][1] is not None:
        yield history
        return
    user_message = history[-1][0]
    # 逐步yield中间history
    for h in process_query_stream(user_message, all_tools, client, history[:-1]):
        yield h

async def check_service_health():
    """检查服务健康状态"""
    # 自定义实现
    pass    

async def get_service_info(service_url):
        # 自定义实现
    return None

def check_services():
    """检查服务状态的包装函数，供Gradio使用"""

    from collections import Counter
    tools = client.list_tools()
    active_services =len(Counter([tool.name.split(".")[0] for tool in tools]))

    active_services = active_services
    total_tools = len(tools)
    services_details = tools

    status_text = f"✅ SCP Hub运行中\n"
    status_text += f"🔌 已连接SCP端侧服务器数: {active_services}\n"
    status_text += f"🛠️ SCP可用工具数: {total_tools}\n\n"
    
    if services_details:
        status_text += "服务详情:\n"
        for service in services_details:
            status = "✅" 
            service_name = service.name
            tools_str = service.description[:60]
            status_text += f"{status} {service_name}  - 工具: {tools_str}\n"

    
    return status_text



async def register_custom_service(url, name, api_key=None):

    if not url:
        return "❌ 请输入有效的服务URL"
    
    # 根据环境适配URL
    adapted_url = adapt_service_url(url)
    
    # 如果name为空，使用URL的一部分作为服务名称
    if not name:
        # 提取URL中的域名部分作为名称
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            name = parsed_url.netloc.split(':')[0] or parsed_url.path.split('/')[1]
        except:
            name = url.split('/')[-2]
    
    # 构建服务配置
    service_config = {
        "name": name,
        "url": url  # 保存原始URL到配置文件，不保存adapted_url
    }
    
    # 如果提供了API密钥，添加到环境变量
    if api_key:
        service_config["env"] = {"API_KEY": api_key}
        
    try:
        async with httpx.AsyncClient() as client:
            print(f"正在注册自定义服务: {name} ({adapted_url})")
            response = await client.post(
                f"{MCP_CLIENT_BASE_URL}/register",
                json={"url": adapted_url, "name": name},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # 保存到mcp.json
                if mcp_config.add_service(service_config):
                    api_key_info = "并配置API密钥" if api_key else ""
                    success_msg = f"✅ 服务注册成功{api_key_info}并保存到mcp.json: {name} ({url}) - {result['message']}"
                else:
                    success_msg = f"✅ 服务注册成功但保存到mcp.json失败: {name} ({url}) - {result['message']}"
                print(success_msg)
                return success_msg
            else:
                error_detail = response.text
                error_msg = f"❌ 服务注册失败: {name} ({url}) - HTTP {response.status_code}\n{error_detail}"
                print(error_msg)
                return error_msg
    except Exception as e:
        error_msg = f"❌ 服务注册出错: {name} ({url}) - {e}"
        print(error_msg)
        return error_msg

def update_services():
    """更新服务状态信息"""
    return check_services()

def show_mcp_json():
    """显示当前mcp.json内容"""
    config = mcp_config.load_config()
    
    if not config or not config.get("mcpServers"):
        return "mcp.json 文件为空或不存在。"
    
    json_content = json.dumps(config, ensure_ascii=False, indent=2)
    return json_content


def create_examples():
    """创建示例查询"""
    return ['''有蛋白质序列：MGQPGNGSAFLLAPNGSHAPDHDVTQERDEVWVVGMGIVMSLIVLAIVFGNVLVITAIAKFERLQTVTNY FITSLACADLVMGLAVVPFGAAHILMKMWTFGNFWCEFWTSIDVLCVTASIETLCVIAVDRYFAITSPFK YQSLLTKNKARVIILMVWIVSGLTSFLPIQMHWYRATHQEAINCYANETCCDFFTNQAYAIASSIVSFYV PLVIMVFVYSRVFQEAKRQLQKIDKSEGRFHVQNLSQVEQDGRTGHGLRRSSKFCLKEHKALKTLGIIMG TFTLCWLPFFIVNIVHVIQDNLIRKEVYILLNWIGYVNSGFNPLIYCRSPDFRIAFQELLCLRRSSLKAY GNGYSSNGNTGEQSGYHVEQEKENKLLCEDLPGTEDFVGHQGTVPSDNIDSQGRNCSTNDSLL，
1、请计算一下序列的消光系数、理论等电位、分子量
2、预测一下清水性和信号肽
3、统计蛋白质参数'''
    ]

# 创建Gradio界面
with gr.Blocks(title="LLM调用SCP-Tools演示", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# LLM调用SCP-Tools演示")
    gr.Markdown("这个演示界面展示了如何使用LLM（如DeepSeek）调用SCP提供的服务。您可以通过输入自然语言查询来获取生物科学类信息。")
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                height=500,
                label="对话记录"
            )
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="输入您的问题或指令，如'计算原子级偏电荷和手性标签的SMILES字符串是CC@HC@@HC。请返回原子级偏电荷和手性标签的SMILES字符串。'",
                    label="输入",
                    scale=7
                )
                submit_btn = gr.Button("发送", variant="primary", scale=1)
            
            with gr.Accordion("示例命令", open=False):
                examples = gr.Examples(
                    examples=create_examples(),
                    inputs=[msg],
                )
                
        with gr.Column(scale=1):
            status_display = gr.Textbox(
                label="服务状态",
                value="正在检查服务状态...",
                lines=10,
                interactive=False
            )
            refresh_btn = gr.Button("刷新状态")
            
            with gr.Accordion("自定义服务注册", open=True):
                service_url = gr.Textbox(
                    placeholder="输入服务URL，例如: http://127.0.0.1:8080/scp",
                    label="服务URL"
                )
                service_name = gr.Textbox(
                    placeholder="输入服务名称（可选）",
                    label="服务名称"
                )
                api_key = gr.Textbox(
                    placeholder="输入API密钥（可选）",
                    label="API密钥",
                    type="password"
                )
                custom_register_btn = gr.Button("注册服务[SCP]", variant="secondary")
            
    
    # 事件处理
    # 使用回调链：先添加用户消息，然后获取机器人响应
    msg.submit(
        add_user_message, 
        inputs=[msg, chatbot], 
        outputs=[msg, chatbot]
    ).then(
        get_bot_response_stream,
        inputs=[chatbot],
        outputs=[chatbot]
    )
    
    submit_btn.click(
        add_user_message, 
        inputs=[msg, chatbot], 
        outputs=[msg, chatbot]
    ).then(
        get_bot_response_stream,
        inputs=[chatbot],
        outputs=[chatbot]
    )
    
    refresh_btn.click(update_services, inputs=[], outputs=[status_display])
   
    # 自定义服务注册
    custom_register_btn.click(
        lambda url, name, key: asyncio.run(register_custom_service(url, name, key)),
        inputs=[service_url, service_name, api_key],
        outputs=[status_display]
    )
    
    
    # 初始化服务状态
    demo.load(check_services, inputs=[], outputs=[status_display])
    # 自动注册服务
    # demo.load(lambda: asyncio.run(register_mcp_services()), inputs=[], outputs=[])

if __name__ == "__main__":
    print("===== SCP服务网页演示 =====")
    # 启动Gradio界面
    demo.launch(share=False, server_name="0.0.0.0", server_port=12345)
