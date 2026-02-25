import json
import logging
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.entrypoint
def main(payload):
    logger.info(f"Received payload: {json.dumps(payload)}")
    
    prompt = payload.get('prompt')
    
    agent = Agent(
        name="TeddieAI",
        system_prompt="You are a helpful assistant.",
    )
    response = agent(prompt)
    
    return response

if __name__ == "__main__":
    logger.info("Starting TeddieAI Agent...")
    app.run()
