import asyncio
from app.ai.config import initialize_ai_environment

async def verify_frontier_agent_loop():
    print("🤖 Triggering system handshake with Google AI Studio using Pydantic Settings...")
    try:
        # Initialize LlamaIndex environment settings mappings
        llm = initialize_ai_environment()
        
        # Test basic asynchronous text completion response cycles
        response = await llm.acomplete(
            "Say the words 'Pydantic AI Connected' in exactly three words."
        )
        print(f"\n🎉 Success! Response from model: {response.text.strip()}")
    except Exception as e:
        print(f"\n❌ Setup validation check failed. Details: {str(e)}")

if __name__ == "__main__":
    asyncio.run(verify_frontier_agent_loop())


