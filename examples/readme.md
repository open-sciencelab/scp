# SCP Experiment Examples

## Experiment 1: End-to-End Asynchronous Experiment Orchestration

### Overview
Scientific discovery experiments, particularly those involving wet/dry lab operations, pose unique challenges due to their **long execution durations** and **high operational costs**, coupled with strict permission management requirements. To address these pain points, this solution leverages asynchronous mechanisms, a centralized Hub for task coordination, and Redis middleware for reliable result propagation.

### Challenges in Scientific Discovery Experiments
- **Extended Runtime**: Experiments often run for extended periods (hours/days), increasing risks of connection interruptions, timeouts, or data loss during transmission.
- **High Operational Costs**: Resource-intensive operations (e.g., large-scale simulations, instrument control) demand efficient resource allocation and strict access control.
- **Permission Sensitivity**: Secure access to experimental tools, data, and infrastructure is critical to prevent unauthorized modifications or data leaks.

### SCP's Optimized Solution
To mitigate the above challenges, SCP (Scientific Computing Platform) implements an **asynchronous task management framework** with a Hub-and-Spoke architecture and Redis-backed result streaming. Key features include:

#### 1. Asynchronous Task Execution
Avoids connection drops and data loss by decoupling task submission from execution. Long-running tasks are managed as background processes, with progress and results propagated asynchronously.

#### 2. Hub-Based Coordination & Permission Verification
A centralized Hub server acts as the "traffic controller," ensuring secure task distribution, resource allocation, and access validation before task execution on edge servers.

#### 3. Redis Middleware for Result Streaming
Intermediate and final results are stored in Redis, enabling real-time subscription-based retrieval by users. This eliminates blocking waits and ensures data integrity even if edge servers disconnect temporarily.

### Core Workflow

#### Phase 1: Task Distribution
1. **Tool Discovery**: The Hub server queries available asynchronous tools (e.g., experiment controllers, data processors) and their metadata (capabilities, resource requirements).
2. **Instruction Issuance**: Users submit tasks via tool_call APIs, specifying parameters (e.g., experiment type, input data, priority).
3. **Task Routing**: The Hub validates user permissions, matches tasks with compatible edge servers (based on resource availability), and dispatches the task payload.
4. **Execution Initiation**: Edge servers acknowledge receipt, perform pre-execution checks (e.g., environment setup, dependency validation), and start the task.

#### Phase 2: Result Propagation
1. **Intermediate Result Caching**: As tasks progress, intermediate outputs (e.g., raw sensor data, partial analysis) are pushed to Redis with unique task IDs and timestamps.
2. **User Subscription**: Users subscribe to Redis channels (via SUB commands) using their task IDs. The Hub notifies users when new results are available.
3. **Final Result Delivery**: Upon task completion, the edge server pushes the final result to Redis and triggers a user alert (e.g., WebSocket notification). Users retrieve the full result set from Redis.

### Key Technologies

| Component | Purpose |
|-----------|---------|
| **Asynchronous Tools** | Execute long-running tasks without blocking user connections |
| **Hub Server** | Centralizes task routing, permission checks, and resource orchestration (built with Flask) |
| **Edge Server** | Edge-side task distribution system |
| **Edge Server Workers** | Execute specific tasks |
| **Redis** | Acts as a high-speed message broker for real-time result streaming and task state tracking |
| **Message Queue (MQ)** | Task decoupling to improve concurrency capabilities of individual modules |

### Benefits
- **Fault Tolerance**: Asynchronous execution prevents connection timeouts, ensuring tasks complete even if client sessions drop
- **Efficiency**: Resource allocation via the Hub minimizes idle time and reduces operational costs
- **Security**: Strict permission verification at the Hub layer mitigates unauthorized access risks
- **Real-Time Visibility**: Redis streaming provides instant access to intermediate results, accelerating decision-making

### Quick Start

#### 1. Start Hub Server
```bash
cd scp/examples/SEO(SCP-Experiment-Orchestration)
python hub.py
```

#### 2. Start Edge Server
```bash
cd scp/examples/SEO(SCP-Experiment-Orchestration)
python lab_server.py
```

#### 3. Start Edge Server Workers
```bash
cd scp/examples/SEO(SCP-Experiment-Orchestration)
python lab_server_thread.py
```

#### 4. Client Demo
```python
from scp.lab.client import SciLabClient

def example():
    try:
        # Create client
        client = SciLabClient("http://127.0.0.1:8081")
        servers = client.list_servers()
        print(servers)

        tools = client.list_tools()
        print(tools)

        # Call a tool
        result = client.call_tool("git-demo.predict_signalpeptide", {
            "protein": "MGQPGNGSAFLLAPNGSHAPDHDVTQERDEVWVVGMGIVMSLIVLAIVFGNVLVITAIAKFERLQTVTNY..."
        })
        print(result)
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    example()
```

---

## Experiment 2: LLM Tool Invocation

This experiment demonstrates how Large Language Models (LLMs) can invoke SCP tools for scientific computing tasks.

### Prerequisites

#### 1. Apply for DeepSeek API Key
1. Navigate to [DeepSeek Platform](https://platform.deepseek.com/usage)
2. Follow the DeepSeek registration and setup steps
3. Obtain your corresponding API key

#### 2. Configure API Key
1. Navigate to `scp/examples/SEO(SCP-Experiment-Orchestration)/toolcall_web.py`
2. Replace the API key on line 11 with your own API key

#### 3. Start LLM Tool Invocation Demo
```bash
cd scp/examples/SEO(SCP-Experiment-Orchestration)
python toolcall_web.py
```

### Usage Flow

1. **Setup Environment**: Configure your DeepSeek API credentials
2. **Launch Services**: Start the required hub and edge servers as described in Experiment 1
3. **Run LLM Demo**: Execute the tool invocation demo to see how LLMs interact with SCP tools
4. **Monitor Results**: Observe real-time task execution and result streaming through the Redis-backed system

### Features

- **Natural Language Interface**: LLMs can interpret scientific requests and map them to appropriate SCP tools
- **Intelligent Tool Selection**: Automatic selection of optimal tools based on task requirements
- **Contextual Parameter Passing**: Smart extraction of parameters from natural language descriptions
- **Result Interpretation**: LLMs can process and explain scientific results in human-readable format

---

## Additional Resources

- **API Documentation**: Refer to the SCP API documentation for detailed endpoint specifications
- **Tool Development**: See the developer guide for creating custom scientific computing tools
- **Performance Tuning**: Check the configuration guide for optimizing system performance
- **Troubleshooting**: Visit the FAQ section for common issues and solutions
