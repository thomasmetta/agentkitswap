# Crypto Chatbot Agent

This uses the CDP Agentkit LangChain python sample code as the foundation. This adds the flask web server to allow for the chatbot to be accessed via a web interface.

- Add custom agent capacity like supply liquidity and withdrawal for AAVE
- Added a custom prompt for automating portfolio and the prompt will deposit ETH to AAVE depending on how much ETH the user hold

## Ask the chatbot to engage in the Web3 ecosystem and interact with DeFi!

- "What is my wallet address?"
- "What is my balance?"
- "What is my portfolio?"
- "Supply 0.1 ETH to AAVE"
- "Withdraw 0.1 ETH from AAVE"
- "Automate my portfolio"

## Requirements

- Python 3.10+
- Poetry for package management and tooling
  - [Poetry Installation Instructions](https://python-poetry.org/docs/#installation)
- [CDP API Key](https://portal.cdp.coinbase.com/access/api)
- [OpenAI API Key](https://platform.openai.com/docs/quickstart#create-and-export-an-api-key)

### Checking Python Version

Before using the example, ensure that you have the correct version of Python installed. The example requires Python 3.10 or higher. You can check your Python version by running the following code:

```bash
python --version
poetry --version
```

## Installation

```bash
poetry install
```

## Run the flask server for the chatbot

### Set ENV Vars

- Ensure the following ENV Vars are set:
  - "CDP_API_KEY_NAME"
  - "CDP_API_KEY_PRIVATE_KEY"
  - "OPENAI_API_KEY"
  - "NETWORK_ID" (Defaults to `base-sepolia`)

```bash
poetry run python api.py
```

## Run the frontend

```bash
cd react-chatbot-app
npm install
npm run dev
```
