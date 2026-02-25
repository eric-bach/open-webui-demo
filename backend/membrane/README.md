# AgentCore Runtime Template

This template provides a basic implementation of an agent using the AgentCore Runtime.  Use this template for use cases that do not require any LLM inference or agentic reasoning, such as simple data processing or automation tasks.

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Installation

Create a virtual environment and install dependencies:
    ```bash
    uv sync
    ```

### Running the Agent locally

    ```bash
    uv run src/main.py
    ```

### Testing the Agent locally

    ```bash
    curl -X POST http://localhost:8080/invocations -H "Content-Type: application/json" -d '{"prompt": "Hello AgentCore"}'
    ```

### Deploying the Agent

    Agents are deployed to AWS Bedrock AgentCore using the automated pipeline.  Please push the code to the main branch to trigger the pipeline.
    
### Testing the deployed Agent

    ```bash
    aws bedrock-agentcore invoke-agent-runtime --agent-runtime-arn <AGENTCORE_RUNTIME_ARN> --qualifier DEFAULT --payload $(echo '{"prompt": "Hello AgentCore"}' | base64) response.json 
    ```
