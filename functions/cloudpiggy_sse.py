# This Open WebUI pipe function is used to connect to the Cloud Piggy backend when SSE is enabled
import boto3
import json
import uuid
from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator, Iterable, Any


class Pipe:
    class Valves(BaseModel):
        AWS_REGION: str = Field(default="us-west-2")
        AGENT_RUNTIME_ARN: str = Field(
            default="arn:aws:bedrock-agentcore:us-west-2:703481943173:runtime/aicoe_cloud_piggy_agent_dev-TP79Y44gEV"
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

        def _maybe_unescape_string(s: str) -> str:
            """
            If s looks like a JSON-encoded string literal (e.g. "\"hello\\n\""),
            decode it into a normal Python string ("hello\n").
            """
            if not isinstance(s, str):
                return s
            t = s.strip()
            if len(t) >= 2 and (
                (t[0] == '"' and t[-1] == '"') or (t[0] == "'" and t[-1] == "'")
            ):
                try:
                    return json.loads(t)
                except Exception:
                    return s
            return s

        def _normalize_stream_text(text: str) -> str:
            if not isinstance(text, str) or not text:
                return text

            # Unescape common SSE/JSON newlines FIRST
            text = text.replace("\\n", "\n").replace("\\\\n", "\n")

            # Ultra-aggressive: remove ALL quotes (AgentCore artifacts dominate)
            text = text.replace('"', "")

            # Remove doubled artifacts
            text = text.replace('""', "").replace("  ", " ")  # Normalize double spaces

            # Preserve spaces: lstrip/rstrip only, no full strip yet
            return text.lstrip().rstrip()

        def _extract_text(obj: Any) -> Optional[str]:
            """
            Try common shapes for streamed deltas. Adjust once you know your exact schema.
            """
            if isinstance(obj, str):
                return obj

            if isinstance(obj, dict):
                # Simple keys
                for k in ("output", "text", "content", "message"):
                    v = obj.get(k)
                    if isinstance(v, str):
                        return v

                # Common "delta" patterns
                delta = obj.get("delta")
                if isinstance(delta, str):
                    return delta
                if isinstance(delta, dict):
                    for k in ("text", "content", "output"):
                        v = delta.get(k)
                        if isinstance(v, str):
                            return v

                # OpenAI-ish nesting: {"choices":[{"delta":{"content":"..."}}]}
                choices = obj.get("choices")
                if isinstance(choices, list) and choices:
                    c0 = choices[0]
                    if isinstance(c0, dict):
                        d = c0.get("delta")
                        if isinstance(d, dict):
                            v = d.get("content")
                            if isinstance(v, str):
                                return v

            return None

        def _yield_sse_data(data_str: str) -> Iterable[str]:
            """
            Parse one SSE event's aggregated 'data:' payload.
            Handles:
              - raw text
              - JSON objects
              - double-encoded JSON string fields
              - token-separator quote noise
            """
            data_str = data_str.strip()
            if not data_str or data_str in ("[DONE]", "DONE"):
                return

            # JSON envelope
            if data_str[:1] in ("{", "["):
                try:
                    obj = json.loads(data_str)
                except json.JSONDecodeError:
                    # raw text; unescape + normalize
                    txt = _normalize_stream_text(_maybe_unescape_string(data_str))
                    if txt:
                        yield txt
                    return

                text = _extract_text(obj)
                if isinstance(text, str):
                    # Handle double-encoded strings, then normalize quote-noise
                    text = _maybe_unescape_string(text)
                    text = _normalize_stream_text(text)
                    if text:
                        yield text
                    return

                # If you want to inspect schema, temporarily enable:
                # yield json.dumps(obj, ensure_ascii=False)
                return

            # Raw text fallback
            txt = _normalize_stream_text(_maybe_unescape_string(data_str))
            if txt:
                yield txt

        def generate_response() -> Generator[str, None, None]:
            try:
                response = client.invoke_agent_runtime(
                    agentRuntimeArn=self.valves.AGENT_RUNTIME_ARN,
                    runtimeSessionId=session_id,
                    payload=payload_bytes,
                    contentType="application/json",
                    accept="text/event-stream",
                )

                content_type = (response.get("contentType") or "").lower()
                stream = response["response"]

                if "text/event-stream" in content_type:
                    event_data_lines = []

                    for raw_line in stream.iter_lines(chunk_size=1024):
                        if raw_line is None or raw_line == b"":
                            if event_data_lines:
                                data_payload = "\n".join(
                                    event_data_lines
                                )  # ACTUAL \n, not "\\n"
                                for out in _yield_sse_data(data_payload):
                                    yield out
                                event_data_lines = []
                            continue

                        line = raw_line.decode("utf-8", errors="replace").rstrip()
                        if line.strip() == "":
                            if event_data_lines:
                                data_payload = "\n".join(event_data_lines)
                                for out in _yield_sse_data(data_payload):
                                    yield out
                                event_data_lines = []
                            continue

                        if line.startswith("data:"):
                            event_data_lines.append(line[5:].lstrip())

                    # Flush trailing buffered event
                    if event_data_lines:
                        data_payload = "\n".join(event_data_lines)
                        for out in _yield_sse_data(data_payload):
                            yield out

                else:
                    # Non-SSE fallback
                    for raw_line in stream.iter_lines(chunk_size=1024):
                        if raw_line:
                            txt = raw_line.decode("utf-8", errors="replace")
                            txt = _normalize_stream_text(_maybe_unescape_string(txt))
                            if txt:
                                yield txt

            except Exception as e:
                yield f"**AgentCore Error:** {str(e)}"

        return generate_response()