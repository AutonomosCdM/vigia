import agentops

print("AgentOps available methods:")
print(dir(agentops))
print("\n" + "="*50)

try:
    from agentops.sdk.decorators import trace
    print("✅ trace import: OK")
    print("trace methods:", dir(trace))
except Exception as e:
    print(f"❌ trace import failed: {e}")

print("\n" + "="*50)

try:
    # Test basic initialization
    agentops.init(api_key="995199e8-36e5-47e7-96b9-221a3ee12fb9", auto_start_session=False)
    print("✅ AgentOps initialization: OK")
    
    # Test session start
    session = agentops.start_session(tags=["test"])
    print("✅ Session start: OK")
    print("Session type:", type(session))
    
except Exception as e:
    print(f"❌ AgentOps test failed: {e}")