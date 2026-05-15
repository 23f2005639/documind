"""Test script to verify all 5 OpenRouter LLMs are accessible."""

import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

MODELS = {
    "Analyzer": "deepseek/deepseek-v4-flash:free",
    "Supervisor": "arcee-ai/trinity-large-thinking:free",
    "Writer": "baidu/cobuddy:free",
    "Query": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "Fallback": "poolside/laguna-m.1:free",
}


def test_model(name: str, model_id: str) -> bool:
    """Test a single OpenRouter model."""
    start_time = time.time()
    try:
        llm = ChatOpenAI(
            model=model_id,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1,
        )
        response = llm.invoke("say hello")
        elapsed = time.time() - start_time
        print(f"✅ {name:12} ({model_id}): {response.content[:50]} [{elapsed:.2f}s]")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ {name:12} ({model_id}): {str(e)[:80]} [{elapsed:.2f}s]")
        return False


if __name__ == "__main__":
    print("Testing OpenRouter LLM access...\n")
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in .env file")
        print("Create .env file with: OPENROUTER_API_KEY=sk-or-your-key-here")
        exit(1)
    
    results = [test_model(name, model_id) for name, model_id in MODELS.items()]
    
    print(f"\n{'='*60}")
    print(f"Result: {sum(results)}/{len(results)} models accessible")
    print(f"{'='*60}")
    
    if sum(results) == len(results):
        print("✓ All models working! Ready to build DocuMind.")
    else:
        print("✗ Some models failed. Check your API key and OpenRouter status.")
        exit(1)

# Made with Bob
