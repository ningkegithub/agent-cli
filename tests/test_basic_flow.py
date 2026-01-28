import sys
import os
from langchain_core.messages import HumanMessage

# Add current directory to path so we can import agent_core
sys.path.append(os.getcwd())

try:
    from agent_core import build_graph
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def test_graph_execution():
    print("🧪 Starting Integration Test...")
    
    # Check API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found. Test might fail due to auth.")

    try:
        app = build_graph()
        print("✅ Graph built successfully.")
    except Exception as e:
        print(f"❌ Graph build failed: {e}")
        sys.exit(1)

    # Simulating a user input
    # We ask a simple question first to avoid complex skill loading issues if paths are wrong
    inputs = {
        "messages": [HumanMessage(content="Hello! Who are you?")],
        "active_skills": {}
    }

    print("🔄 Running graph invoke...")
    try:
        # We use invoke instead of stream for a quick check
        result = app.invoke(inputs)
        
        last_msg = result["messages"][-1]
        print(f"🤖 Final Response: {last_msg.content}")
        print("✅ Integration Test: SUCCESS")
             
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_graph_execution()
