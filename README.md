# Open WebUI

This project demonstrates the use of Open WebUI for connecting and limiting access to various backend APIs.

## Getting Started

### Prerequisites

- uv
- Python 3.12
- Ollama
- Docker
- Docker Compose

### Deploy backend

1. Go to each of the backend directories
2. Run `uv sync`
3. Go to the infrastructure directory
4. Run `uv sync`
5. Run `./deploy.sh`

For Cloud Piggy, the agent is deployed in the Agentic Platform.

### Run frontend

1. Edit the `docker-compose.yml` file to set the `WEBUI_SECRET_KEY` environment variable to a random string
2. Run `docker-compose up -d`

## Usage

1. Open [http://localhost:3000](http://localhost:3000) in your browser
2. Sign up for an account
3. Log in
4. Start using Open WebUI

## Configuration

### Create users and groups

1. In the Admin Settings -> Users, create additional users
2. In the Admin Settings -> Users -> Groups, create and assign users to groups
3. In the Admin Settings -> Functions, create the pipes for each backend

### Add the following pipe functions in Open WebUI

1. In Admin Settings -> Functions, create the pipes for each backend
   ```
   functions\cloudpiggy.py
   functions\membrane.py
   functions\teddieai.py
   ```
2. Enable each function
3. Click the gear and set the environment variables for the API URL or AgentCore Runtime ARN

### Assign groups to models

1. In Admin Settings -> Settings -> Models and edit the model
2. Click the lock icon and select the group that should have access to the model
3. Click the save icon
