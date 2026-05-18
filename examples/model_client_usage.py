#!/usr/bin/env python3
"""
Model Client Usage Examples

Demonstrates both Gateway and Direct modes for the unified model client.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.llm.model_client import ModelClient  # noqa: E402
from src.core.llm.model_utils import ClientMode, Message, ToolDefinition  # noqa: E402

load_dotenv()


async def example_gateway_mode():
    """
    Gateway Mode Example

    User configures `.agent/config.json` with:
      - model
      - gateway_url
      - gateway_key

    The gateway handles all provider routing internally.
    """
    print("\n=== Gateway Mode ===")

    # Option 1: Auto-detect from project config
    client = await ModelClient.create()

    # Option 2: Explicit configuration
    # config = ClientConfig(
    #     mode=ClientMode.GATEWAY,
    #     gateway_url="http://localhost:8000",
    #     gateway_key="your-key",
    #     model="gemini-2.5-flash",
    # )
    # client = await ModelClient.create(config)

    try:
        # Simple chat
        response = await client.chat([
            Message(role="user", content="What is 2+2?")
        ])
        print(f"Response: {response.content}")
        print(f"Usage: {response.usage}")

        # List available models
        models = await client.list_models()
        print(f"\nAvailable models: {len(models)}")
        for m in models[:5]:
            print(f"  - {m['id']} ({m.get('provider', 'unknown')})")

    finally:
        await client.close()


async def example_direct_mode():
    """
    Direct Mode Example

    User configures `.agent/config.json` with:
      - model
      - google_api_key
      - openai_api_key
      - anthropic_api_key

    The client auto-routes based on model name prefix.
    """
    print("\n=== Direct Mode ===")

    # Option 1: Auto-detect from project config
    client = await ModelClient.create()

    # Option 2: Explicit configuration
    # config = ClientConfig(
    #     mode=ClientMode.DIRECT,
    #     google_api_key="your-google-key",
    #     openai_api_key="your-openai-key",
    #     anthropic_api_key="your-anthropic-key",
    #     model="gemini-2.5-flash-preview",
    # )
    # client = await ModelClient.create(config)

    try:
        # Chat with different providers - auto-routed by model name
        providers_models = [
            ("Google", "gemini-2.5-flash-preview"),
            ("OpenAI", "gpt-4o-mini"),
            ("Anthropic", "claude-3-5-haiku-20241022"),
        ]

        for provider, model in providers_models:
            try:
                response = await client.chat(
                    messages=[Message(role="user", content="Say hello in one word.")],
                    model=model,
                )
                print(f"{provider} ({model}): {response.content}")
            except Exception as e:
                print(f"{provider} ({model}): Error - {e}")

    finally:
        await client.close()


async def example_with_tools():
    """
    Example using tools/function calling.

    Works the same in both modes - the unified API handles
    provider-specific tool call formats.
    """
    print("\n=== Tool Calling Example ===")

    client = await ModelClient.create()

    # Define a tool
    weather_tool = ToolDefinition(
        name="get_weather",
        description="Get current weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name",
                },
            },
            "required": ["location"],
        },
    )

    try:
        response = await client.chat(
            messages=[
                Message(role="user", content="What's the weather in Tokyo?")
            ],
            tools=[weather_tool],
        )

        if response.has_tool_calls:
            print("Tool calls requested:")
            for tc in response.tool_calls:
                func = tc.get("function", {})
                print(f"  - {func.get('name')}: {func.get('arguments')}")

            # In a real app, you would:
            # 1. Execute the tool
            # 2. Send the result back
            # response = await client.chat([
            #     Message(role="user", content="What's the weather in Tokyo?"),
            #     Message(role="assistant", tool_calls=response.tool_calls),
            #     Message(role="tool", tool_call_id="...", content="Sunny, 25°C"),
            # ])
        else:
            print(f"Response: {response.content}")

    finally:
        await client.close()


async def example_check_mode():
    """
    Check current mode configuration.
    """
    print("\n=== Mode Information ===")

    mode_info = ModelClient.get_mode_info()
    print(f"Current mode: {mode_info['mode']}")

    if mode_info["mode"] == "gateway":
        print(f"  Gateway URL: {mode_info['gateway_url']}")
        print(f"  Has API Key: {mode_info['has_key']}")
    else:
        print("  Configured providers:")
        for provider, configured in mode_info["providers"].items():
            status = "✓" if configured else "✗"
            print(f"    {status} {provider}")


async def main():
    """Run all examples."""
    # Check current mode
    await example_check_mode()

    mode = ModelClient.get_mode()

    if mode == ClientMode.GATEWAY:
        await example_gateway_mode()
    else:
        await example_direct_mode()

    # Tool example works in both modes
    await example_with_tools()


if __name__ == "__main__":
    asyncio.run(main())
