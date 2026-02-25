# requirements: boto3
import boto3
import json
import uuid
import codecs
from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator


class Pipe:
    class Valves(BaseModel):
        AWS_REGION: str = Field(default="us-west-2")
        AGENT_RUNTIME_ARN: str = Field(
            default="arn:aws:bedrock-agentcore:us-west-2:761018860881:runtime/cloud_piggy_agent_dev-l0OxcpANTA"
        )
        AWS_ACCESS_KEY_ID: str = Field(default="")
        AWS_SECRET_ACCESS_KEY: str = Field(default="")

    def __init__(self):
        self.type = "pipe"
        self.id = "agentcore_runtime"
        self.name = "Cloud Piggy Agent"
        self.valves = self.Valves()

    def pipe(
        self, body: dict, __user__: Optional[dict] = None
    ) -> Union[str, Generator[str, None, None], Iterator[str]]:
        messages = body.get("messages", [])
        user_message = messages[-1].get("content", "") if messages else ""

        chat_id = body.get("chat_id", str(uuid.uuid4()))
        session_id = f"owu-{chat_id}".ljust(33, "0")[:64]

        client = boto3.client(
            "bedrock-agentcore",
            region_name=self.valves.AWS_REGION,
            aws_access_key_id=self.valves.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=self.valves.AWS_SECRET_ACCESS_KEY or None,
        )

        payload_bytes = json.dumps({"prompt": user_message}).encode("utf-8")

        def generate_response() -> Generator[str, None, None]:
            try:
                resp = client.invoke_agent_runtime(
                    agentRuntimeArn=self.valves.AGENT_RUNTIME_ARN,
                    runtimeSessionId=session_id,
                    payload=payload_bytes,
                    contentType="application/json",
                    # Even if you “don’t return SSE”, AgentCore streaming often rides on this.
                    accept="text/event-stream",
                )

                stream = resp["response"]

                # Incremental UTF-8 decoder (like TextDecoder(stream=True))
                decoder = codecs.getincrementaldecoder("utf-8")()

                # KEY: use a *tiny* chunk size so nothing waits to fill a 256B buffer
                # If this is too CPU-heavy, try 8, 16, 32.
                CHUNK_SIZE = 8

                for chunk in stream.iter_chunks(chunk_size=CHUNK_SIZE):
                    if not chunk:
                        continue

                    text = decoder.decode(chunk)
                    if text:
                        # Yield immediately; no line buffering, no extra parsing.
                        yield text

                # Flush remaining decoder buffer
                tail = decoder.decode(b"", final=True)
                if tail:
                    yield tail

            except Exception as e:
                yield f"**AgentCore Error:** {str(e)}"

        return generate_response()
