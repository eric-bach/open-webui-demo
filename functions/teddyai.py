import requests
import uuid
from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator


class Pipe:
    class Valves(BaseModel):
        # These fields will show up in the UI settings for you to configure
        API_URL: str = Field(default="https://api.your-org.com/v1/query")
        API_KEY: str = Field(default="")

    def __init__(self):
        self.type = "pipe"
        self.id = "internal_api_bridge"
        self.name = "Organizational Data"
        self.valves = self.Valves()

    def pipe(
        self, body: dict, __user__: Optional[dict] = None
    ) -> Union[str, Generator, Iterator]:
        # Extract the user's last message
        thread_id = str(uuid.uuid4())
        messages = body.get("messages", [])
        user_message = messages[-1].get("content", "") if messages else ""

        # Prepare the request
        headers = {
            "Authorization": f"{self.valves.API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "thread_id": thread_id,
            "message": user_message,
        }

        try:
            # Call the REST API
            response = requests.post(
                self.valves.API_URL, json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Extract the message text and links
            output_list = data.get("output", [])
            if output_list and len(output_list) > 0:
                first_output = output_list[0]
                content_list = first_output.get("content", [])
                text_item = ""
                if content_list and len(content_list) > 0:
                    text_item = content_list[0].get("text", "")

                # Extract and format links
                links = first_output.get("links", [])
                links_md = ""
                if links:
                    links_md = "\n\n**Sources:**\n"
                    for link in links:
                        name = link.get("name", "Document")
                        url = link.get("url", "#")
                        links_md += f"- [{name}]({url})\n"

                return text_item + links_md

            # Fallback if structure doesn't match exactly
            return f"No valid output found. Status: {data.get('status', 'unknown')}. Error: {data.get('error', 'none')}"

        except requests.exceptions.RequestException as e:
            return f"API request failed: {str(e)}"
        except Exception as e:
            return f"Error connecting to internal API: {str(e)}"
