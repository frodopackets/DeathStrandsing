#!/usr/bin/env python3
"""Script to explore Strands SDK structure."""

try:
    from strands import Agent
    from strands.models import BedrockModel
    
    print("=== Agent class ===")
    print("Agent.__init__ signature:")
    import inspect
    print(inspect.signature(Agent.__init__))
    
    print("\n=== BedrockModel class ===")
    print("BedrockModel.__init__ signature:")
    print(inspect.signature(BedrockModel.__init__))
    
    print("\n=== Creating BedrockModel example ===")
    model = BedrockModel(model_id="amazon.nova-pro-v1:0")
    print(f"Model created: {model}")
    
    print("\n=== Creating Agent example ===")
    agent = Agent(model=model)
    print(f"Agent created: {agent}")
    
    print("\n=== Agent methods ===")
    methods = [m for m in dir(agent) if not m.startswith("_")]
    print(f"Available methods: {methods}")
    
    # Check if agent has invoke_async method
    if hasattr(agent, 'invoke_async'):
        print("Agent has invoke_async method")
        print(f"invoke_async signature: {inspect.signature(agent.invoke_async)}")
    
    if hasattr(agent, 'stream_async'):
        print("Agent has stream_async method")
        print(f"stream_async signature: {inspect.signature(agent.stream_async)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()