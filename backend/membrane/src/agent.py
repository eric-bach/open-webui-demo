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
        name="Membrane",
        system_prompt="You are a helpful assistant. In your response, always start with a funny office joke, mention you are Membrane, and then answer the user's question",
    )
    response = agent(prompt)
    
    return response

if __name__ == "__main__":
    logger.info("Starting Membrane Agent...")
    app.run()
