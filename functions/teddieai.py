import requests
from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator


class Pipe:
    class Valves(BaseModel):
        # These fields will show up in the UI settings for you to configure
        API_URL: str = Field(default="https://api.your-org.com/v1/query")
        # API_KEY: str = Field(default="")

    def __init__(self):
        self.type = "pipe"
        self.id = "internal_api_bridge"
        self.name = "Organizational Data"
        self.valves = self.Valves()

    def pipe(
        self, body: dict, __user__: Optional[dict] = None
    ) -> Union[str, Generator, Iterator]:
        # 1. Extract the user's last message
        messages = body.get("messages", [])
        user_message = messages[-1].get("content", "") if messages else ""

        # 2. Prepare the request to your organizational API
        headers = {
            # "Authorization": f"Bearer {self.valves.API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": user_message,
        }

        try:
            # 3. Call your REST API
            response = requests.post(
                self.valves.API_URL, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()

            # 4. Parse your specific JSON structure
            data = response.json()

            return data

        except Exception as e:
            return f"Error connecting to internal API: {str(e)}"
