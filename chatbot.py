import os
import sys
import time

from dotenv import load_dotenv

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Import CDP Agentkit Langchain Extension.
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from decimal import Decimal
from pydantic import BaseModel, Field
from cdp import Wallet
from cdp_langchain.tools import CdpTool

# Configure a file to persist the agent's CDP MPC Wallet Data.
wallet_data_file = "wallet_data.txt"

load_dotenv()


AAVE_POOL_ADDRESS_MAINNET = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
AAVE_POOL_ADDRESS_TESTNET = "0xbE781D7Bdf469f3d94a62Cdcc407aCe106AEcA74"
POOL_DATA_PROVIDER_MAINNET = "0x68100bD5345eA474D93577127C11F39FF8463e93"  # Add actual address
POOL_DATA_PROVIDER_TESTNET = "0x699784A7bbBD29021927B57059c932B10FEb9Bc3"  # Add actual address
POOL_ADDRESSES_PROVIDER_MAINNET = "0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D"
POOL_ADDRESSES_PROVIDER_TESTNET = "0x150E9a8b83b731B9218a5633F1E804BC82508A46"  # Add actual address

SUPPLY_TO_AAVE_PROMPT = """
This tool allows supplying ETH to the Aave V3 protocol through the WETH Gateway on Base network.
The supplied ETH will be automatically wrapped to WETH before being supplied to Aave.
The tool handles both mainnet and testnet environments automatically.
Use this tool when you want to:
- Supply ETH to Aave to earn interest
- Provide collateral for potential borrowing
- Participate in the Aave lending protocol
The tool will:
1. Check if sufficient ETH balance is available
2. Convert ETH to Wei for the transaction
3. Supply the ETH through Aave's WETH Gateway
4. Return the transaction status and hash
"""


class SupplyToAaveInput(BaseModel):
    """Input schema for supplying ETH to Aave."""

    amount: float = Field(
        ...,
        description=
        "Amount of ETH to supply in ETH units (e.g. 0.1 for 0.1 ETH)",
        example=0.1,
        gt=0  # Must be greater than 0
    )


def supply_to_aave(wallet: Wallet, amount: float) -> str:
    """
    Supply ETH to Aave V3 protocol through the WETH Gateway.
    This function only accepts ETH and will wrap it to WETH before supplying.
    Args:
        wallet: The wallet instance to use for the transaction
        amount (float): Amount of ETH to supply in ETH units (e.g. 0.1 for 0.1 ETH)
    Returns:
        str: Status message about the supply operation including the transaction hash if successful
    """
    try:
        # Check if we're on mainnet or testnet
        is_mainnet = wallet.network_id == "base-mainnet"
        WETH_GATEWAY_ADDRESS = "0xd5DDE725b0A2dE43fBDb4E488A7fdA389210d461"
        pool_address = AAVE_POOL_ADDRESS_MAINNET if is_mainnet else AAVE_POOL_ADDRESS_TESTNET

        # Convert amount to Decimal for precise calculation
        amount_decimal = Decimal(str(amount))

        # Check ETH balance
        eth_balance = wallet.balance("eth")
        if eth_balance < amount_decimal:
            return f"Insufficient ETH balance. You have {eth_balance} ETH, but tried to supply {amount_decimal} ETH"

        # Convert ETH to Wei for the transaction
        WEI_PER_ETH = Decimal('1000000000000000000')  # 10^18
        amount_wei = int(amount_decimal * WEI_PER_ETH)

        print('Amount in ETH:', amount_decimal)
        print('Amount in Wei:', amount_wei)
        print('WETH Gateway:', WETH_GATEWAY_ADDRESS)
        print('Pool address:', pool_address)
        print('Wallet address:', wallet.default_address.address_id)

        # Supply ETH through WETH Gateway
        supply_tx = wallet.invoke_contract(
            contract_address=WETH_GATEWAY_ADDRESS,
            method="depositETH",
            args={
                "lendingPool": pool_address,
                "onBehalfOf": wallet.default_address.address_id,
                "referralCode": "0"
            },
            amount=amount_decimal,
            asset_id="eth",
            abi=[{
                "inputs": [{
                    "internalType": "address",
                    "name": "lendingPool",
                    "type": "address"
                }, {
                    "internalType": "address",
                    "name": "onBehalfOf",
                    "type": "address"
                }, {
                    "internalType": "uint16",
                    "name": "referralCode",
                    "type": "uint16"
                }],
                "name":
                "depositETH",
                "outputs": [],
                "stateMutability":
                "payable",
                "type":
                "function"
            }])
        supply_tx.wait()

        network = "mainnet" if is_mainnet else "testnet"
        return f"Successfully supplied {amount_decimal} ETH to Aave on Base {network} with tx: {supply_tx}"
    except Exception as e:
        print('ERROR SUPPLYING:', e)
        return f"Error supplying ETH to Aave: {str(e)}"

WITHDRAWAL_FROM_AAVE_PROMPT = """
This tool allows withdrawing ETH from the Aave V3 protocol through the WETH Gateway on Base sepolia network.
The tool handles both mainnet and testnet environments automatically.
Use this tool when you want to:
- Withdraw ETH from Aave to your wallet
- Withdraw collateral
The tool will:
1. Convert ETH to Wei for the transaction
2. Supply the ETH through Aave's WETH Gateway
3. Return the transaction status and hash
"""


class WithdrawalFromAaveInput(BaseModel):
    """Input schema for withdrawing ETH from Aave."""

    amount: float = Field(
        ...,
        description=
        "Amount of ETH to withdraw in ETH units (e.g. 0.1 for 0.1 ETH)",
        example=0.1,
        gt=0  # Must be greater than 0
    )


def withdrawal_from_aave(wallet: Wallet, amount: float) -> str:
    """
    Withdraw ETH from Aave V3 protocol through the WETH Gateway.
    This function only accepts ETH and will unwrap it to WETH before withdrawing.
    Args:
        wallet: The wallet instance to use for the transaction
        amount (float): Amount of ETH to supply in ETH units (e.g. 0.1 for 0.1 ETH)
    Returns:
        str: Status message about the supply operation including the transaction hash if successful
    """
    try:
        # Check if we're on mainnet or testnet
        is_mainnet = wallet.network_id == "base-mainnet"
        WETH_GATEWAY_ADDRESS = "0xd5DDE725b0A2dE43fBDb4E488A7fdA389210d461"
        pool_address = AAVE_POOL_ADDRESS_MAINNET if is_mainnet else AAVE_POOL_ADDRESS_TESTNET

        # Convert amount to Decimal for precise calculation
        amount_decimal = Decimal(str(amount))

        # Convert ETH to Wei for the transaction
        WEI_PER_ETH = Decimal('1000000000000000000')  # 10^18
        amount_wei = int(amount_decimal * WEI_PER_ETH)

        print('Amount in ETH:', amount_decimal)
        print('Amount in Wei:', amount_wei)
        print('WETH Gateway:', WETH_GATEWAY_ADDRESS)
        print('Pool address:', pool_address)
        print('Wallet address:', wallet.default_address.address_id)

        # Supply ETH through WETH Gateway
        withdrawal_tx = wallet.invoke_contract(
            contract_address=WETH_GATEWAY_ADDRESS,
            method="withdrawETH",
            args={
                "lendingPool": pool_address,
                "amount": str(int(amount_decimal)),
                "to": wallet.default_address.address_id
            },
            amount=amount_decimal,
            asset_id="eth",
            abi=[{
                "inputs": [{
                    "internalType": "address",
                    "name": "lendingPool",
                    "type": "address"
                }, 
                {
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256"
                },
                {
                    "internalType": "address",
                    "name": "to",
                    "type": "address"
                }],
                "name":
                "withdrawETH",
                "outputs": [],
                "stateMutability":
                "nonpayable",
                "type":
                "function"
            }])
        withdrawal_tx.wait()

        network = "mainnet" if is_mainnet else "testnet"
        return f"Successfully withdrew {amount_decimal} ETH from Aave on Base {network} with tx: {withdrawal_tx}"
    except Exception as e:
        print('ERROR WITHDRAWING:', e)
        return f"Error withdrawing ETH from Aave: {str(e)}"



def initialize_agent():
    """Initialize the agent with CDP Agentkit."""
    # Initialize LLM.
    llm = ChatOpenAI(model="gpt-4o-mini")

    wallet_data = None

    if os.path.exists(wallet_data_file):
        with open(wallet_data_file) as f:
            wallet_data = f.read()

    # Configure CDP Agentkit Langchain Extension.
    values = {}
    if wallet_data is not None:
        # If there is a persisted agentic wallet, load it and pass to the CDP Agentkit Wrapper.
        values = {"cdp_wallet_data": wallet_data}

    agentkit = CdpAgentkitWrapper(**values)

    # persist the agent's CDP MPC Wallet Data.
    wallet_data = agentkit.export_wallet()
    with open(wallet_data_file, "w") as f:
        f.write(wallet_data)

    # Initialize CDP Agentkit Toolkit and get tools.
    cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
    tools = cdp_toolkit.get_tools()


    supplyToAaveTool = CdpTool(
        name="supply_to_aave",
        description=SUPPLY_TO_AAVE_PROMPT,
        cdp_agentkit_wrapper=agentkit,
        args_schema=SupplyToAaveInput,
        func=supply_to_aave,
    )

    withdrawalFromAaveTool = CdpTool(
        name="withdrawal_from_aave",
        description=WITHDRAWAL_FROM_AAVE_PROMPT,
        cdp_agentkit_wrapper=agentkit,
        args_schema=WithdrawalFromAaveInput,
        func=withdrawal_from_aave,
    )

    # Add to tools list
    tools.append(supplyToAaveTool)
    tools.append(withdrawalFromAaveTool)
    # Store buffered conversation history in memory.
    memory = MemorySaver()
    config = {"configurable": {"thread_id": "CDP Agentkit Chatbot Example!"}}

    # Create ReAct Agent using the LLM and CDP Agentkit tools.
    return create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier=(
            "You are a helpful agent that can interact onchain using the Coinbase Developer Platform AgentKit. "
            "You are empowered to interact onchain using your tools. If you ever need funds, you can request "
            "them from the faucet if you are on network ID 'base-sepolia'. If not, you can provide your wallet "
            "details and request funds from the user. Before executing your first action, get the wallet details "
            "to see what network you're on. If there is a 5XX (internal) HTTP error code, ask the user to try "
            "again later. If someone asks you to do something you can't do with your currently available tools, "
            "you must say so, and encourage them to implement it themselves using the CDP SDK + Agentkit, "
            "recommend they go to docs.cdp.coinbase.com for more information. Be concise and helpful with your "
            "responses. Refrain from restating your tools' descriptions unless it is explicitly requested."
        ),
    ), config


# Autonomous Mode
def run_autonomous_mode(agent_executor, config, interval=10):
    """Run the agent autonomously with specified intervals."""
    print("Starting autonomous mode...")
    while True:
        try:
            # Provide instructions autonomously
            thought = (
                "Be creative and do something interesting on the blockchain. "
                "Choose an action or set of actions and execute it that highlights your abilities."
            )

            # Run agent in autonomous mode
            for chunk in agent_executor.stream(
                {"messages": [HumanMessage(content=thought)]}, config
            ):
                if "agent" in chunk:
                    print(chunk["agent"]["messages"][0].content)
                elif "tools" in chunk:
                    print(chunk["tools"]["messages"][0].content)
                print("-------------------")

            # Wait before the next action
            time.sleep(interval)

        except KeyboardInterrupt:
            print("Goodbye Agent!")
            sys.exit(0)


# Chat Mode
def run_chat_mode(agent_executor, config):
    """Run the agent interactively based on user input."""
    print("Starting chat mode... Type 'exit' to end.")
    while True:
        try:
            user_input = input("\nPrompt: ")
            if user_input.lower() == "exit":
                break

            # Run agent with the user's input in chat mode
            for chunk in agent_executor.stream(
                {"messages": [HumanMessage(content=user_input)]}, config
            ):
                if "agent" in chunk:
                    print(chunk["agent"]["messages"][0].content)
                elif "tools" in chunk:
                    print(chunk["tools"]["messages"][0].content)
                print("-------------------")

        except KeyboardInterrupt:
            print("Goodbye Agent!")
            sys.exit(0)


# Mode Selection
def choose_mode():
    """Choose whether to run in autonomous or chat mode based on user input."""
    while True:
        print("\nAvailable modes:")
        print("1. chat    - Interactive chat mode")
        print("2. auto    - Autonomous action mode")

        choice = input("\nChoose a mode (enter number or name): ").lower().strip()
        if choice in ["1", "chat"]:
            return "chat"
        elif choice in ["2", "auto"]:
            return "auto"
        print("Invalid choice. Please try again.")


def main():
    """Start the chatbot agent."""
    agent_executor, config = initialize_agent()

    mode = choose_mode()
    if mode == "chat":
        run_chat_mode(agent_executor=agent_executor, config=config)
    elif mode == "auto":
        run_autonomous_mode(agent_executor=agent_executor, config=config)


if __name__ == "__main__":
    print("Starting Agent...")
    main()
