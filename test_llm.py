import os
from ghost_query.agent.llm_client import LLMClient

def test_llm():
    # Force Mock Environment Variables to simulate Groq fallback
    os.environ["API_BASE_URL"] = ""
    os.environ["MODEL_NAME"] = "llama-3.3-70b-versatile" 
    
    # Check if a real key exists before making an actual API call, to avoid blind failure
    real_key = os.environ.get("GROQ_API_KEY")
    if real_key:
        os.environ["HF_TOKEN"] = real_key
        client = LLMClient()
        print(f"Instantiated: {client.mode}")
        
        # Test Generation
        response = client.generate("Answer in exactly one word: What is 2+2?")
        print(f"Response: {response}")
        assert "4" in response or "four" in response.lower(), "Unexpected LLM output!"
        print("✅ LLM Connection Successful!")
    else:
        print("Skipping active inference test due to missing GROQ_API_KEY globally.")

if __name__ == "__main__":
    test_llm()
