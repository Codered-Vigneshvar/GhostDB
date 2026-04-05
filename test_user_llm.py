import os
from ghost_query.agent.llm_client import LLMClient
from dotenv import load_dotenv

def test_llm_execution():
    # Attempt to load local environment securely
    load_dotenv(override=True)
    
    # We will temporarily map GROQ_API_KEY to HF_TOKEN if token is missing
    # this just guarantees the test completes using the key already configured historically
    if not os.environ.get("HF_TOKEN") and os.environ.get("GROQ_API_KEY"):
        os.environ["HF_TOKEN"] = os.environ.get("GROQ_API_KEY")
        
    if not os.environ.get("MODEL_NAME"):
        os.environ["MODEL_NAME"] = "llama-3.3-70b-versatile"
        
    try:
        llm = LLMClient()
        response = llm.generate("Say hello in one sentence.")
        print(f"\n--- SUCCESS ---")
        print(f"Endpoint Used: {llm.mode}")
        print(f"Response: {response}")
    except Exception as e:
        print(f"\n--- FAILED ---")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_llm_execution()
