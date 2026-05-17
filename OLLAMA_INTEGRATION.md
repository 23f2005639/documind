# Ollama Cloud Integration Guide

## Overview

This document provides detailed information about integrating Ollama Cloud API into DocuMind for free-tier LLM operations.

## Ollama Cloud vs Local Ollama

### Ollama Cloud (Recommended for MVP)
- **Pros**:
  - No local compute requirements
  - Managed infrastructure
  - Consistent performance
  - Easy scaling
  - No GPU needed
  
- **Cons**:
  - Requires internet connection
  - Potential rate limits
  - API costs (though free tier available)

### Local Ollama
- **Pros**:
  - Completely free
  - No rate limits
  - Full control
  - Works offline
  
- **Cons**:
  - Requires significant compute (8GB+ RAM, GPU recommended)
  - Slower inference without GPU
  - Manual model management
  - Higher latency for large models

## Ollama Cloud API Setup

### Step 1: Account Creation

**Note**: As of early 2024, Ollama Cloud is in development. This guide assumes the API will follow OpenAI-compatible patterns.

1. Visit [ollama.ai](https://ollama.ai) or the Ollama Cloud portal
2. Sign up for an account
3. Navigate to API settings
4. Generate an API key
5. Note your API endpoint URL

### Step 2: Free Tier Limits (Estimated)

Based on typical cloud LLM providers, expected limits:

- **Requests**: 100-500 requests/day
- **Tokens**: 50K-100K tokens/day
- **Rate Limit**: 3-10 requests/minute
- **Models**: Access to smaller models (7B-13B parameters)
- **Context Window**: 4K-8K tokens

**Optimization Strategies**:
- Cache responses for identical queries
- Use smaller models for simple tasks
- Batch documentation generation
- Implement request queuing
- Use local fallback for development

### Step 3: API Configuration

Add to `.env`:

```bash
# Ollama Cloud Configuration
OLLAMA_API_KEY=your-api-key-here
OLLAMA_BASE_URL=https://api.ollama.cloud/v1
OLLAMA_MODEL=llama3.1:8b

# Fallback to local Ollama
OLLAMA_LOCAL_URL=http://localhost:11434
USE_LOCAL_OLLAMA=false

# Rate Limiting
OLLAMA_MAX_REQUESTS_PER_MINUTE=10
OLLAMA_MAX_TOKENS_PER_DAY=50000

# Caching
ENABLE_LLM_CACHE=true
CACHE_TTL_HOURS=24
```

## Implementation

### LLM Service with Ollama Cloud

Create `backend/app/services/llm.py`:

```python
import httpx
import structlog
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential
from functools import lru_cache
import hashlib
import json

from app.config import settings

logger = structlog.get_logger()


class OllamaLLMService:
    """Service for interacting with Ollama Cloud API"""
    
    def __init__(self):
        self.api_key = settings.ollama_api_key
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.local_url = getattr(settings, 'ollama_local_url', 'http://localhost:11434')
        self.use_local = getattr(settings, 'use_local_ollama', False)
        
        # Rate limiting
        self.max_requests_per_minute = getattr(settings, 'ollama_max_requests_per_minute', 10)
        self.request_count = 0
        self.last_reset = None
        
        # Token tracking
        self.tokens_used_today = 0
        self.max_tokens_per_day = getattr(settings, 'ollama_max_tokens_per_day', 50000)
        
        logger.info(
            "Initialized Ollama LLM service",
            model=self.model,
            use_local=self.use_local
        )
    
    def _get_cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key for prompt"""
        cache_data = {
            "prompt": prompt,
            "model": self.model,
            **kwargs
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    @lru_cache(maxsize=1000)
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available"""
        # In production, use Redis or similar
        return None
    
    def _cache_response(self, cache_key: str, response: str):
        """Cache response"""
        # In production, use Redis with TTL
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        Generate text using Ollama Cloud API
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        # Check cache
        if getattr(settings, 'enable_llm_cache', True):
            cache_key = self._get_cache_key(prompt, system_prompt=system_prompt, temperature=temperature)
            cached = self._get_cached_response(cache_key)
            if cached:
                logger.info("Using cached LLM response", cache_key=cache_key)
                return cached
        
        # Check rate limits
        if self.tokens_used_today >= self.max_tokens_per_day:
            logger.warning("Daily token limit reached, using fallback")
            if self.use_local:
                return await self._generate_local(prompt, system_prompt, temperature, max_tokens)
            raise Exception("Daily token limit exceeded")
        
        try:
            if self.use_local:
                response = await self._generate_local(prompt, system_prompt, temperature, max_tokens)
            else:
                response = await self._generate_cloud(prompt, system_prompt, temperature, max_tokens, stream)
            
            # Cache response
            if getattr(settings, 'enable_llm_cache', True):
                self._cache_response(cache_key, response)
            
            # Track tokens (approximate)
            estimated_tokens = len(prompt.split()) + len(response.split())
            self.tokens_used_today += estimated_tokens
            
            logger.info(
                "Generated LLM response",
                prompt_length=len(prompt),
                response_length=len(response),
                tokens_used_today=self.tokens_used_today
            )
            
            return response
            
        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            # Fallback to local if cloud fails
            if not self.use_local:
                logger.info("Falling back to local Ollama")
                return await self._generate_local(prompt, system_prompt, temperature, max_tokens)
            raise
    
    async def _generate_cloud(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> str:
        """Generate using Ollama Cloud API"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _generate_local(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using local Ollama instance"""
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.local_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "temperature": temperature,
                    "options": {
                        "num_predict": max_tokens
                    }
                }
            )
            response.raise_for_status()
            
            # Ollama returns streaming JSON, combine responses
            result = ""
            for line in response.text.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    result += data.get("response", "")
            
            return result
    
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured output (JSON)
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            schema: JSON schema for output validation
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response
        """
        # Add JSON formatting instruction
        json_prompt = f"{prompt}\n\nRespond with valid JSON only."
        if schema:
            json_prompt += f"\n\nFollow this schema: {json.dumps(schema)}"
        
        response = await self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for structured output
            **kwargs
        )
        
        # Extract JSON from response
        try:
            # Try to find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e), response=response)
            raise ValueError(f"Invalid JSON response: {e}")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for text
        Note: Ollama Cloud may not support embeddings, use sentence-transformers instead
        """
        raise NotImplementedError("Use EmbeddingService for embeddings")


# Singleton instance
llm_service = OllamaLLMService()
```

### Prompt Templates for Documentation

Create `backend/app/services/prompts.py`:

```python
"""Prompt templates for documentation generation"""

DOCUMENTATION_SYSTEM_PROMPT = """You are an expert technical writer and software architect. Your task is to generate comprehensive, clear, and accurate documentation for code changes.

Guidelines:
1. Write in clear, concise language
2. Include practical examples
3. Explain the "why" not just the "what"
4. Highlight important considerations
5. Use proper markdown formatting
6. Include code snippets with syntax highlighting
7. Cross-reference related components
8. Consider the audience (developers)

Output Format:
- Use markdown with proper headings
- Include code blocks with language tags
- Use bullet points for lists
- Add callouts for warnings/tips
- Keep paragraphs short and focused
"""


def create_documentation_prompt(
    change_report: dict,
    context: str,
    related_code: list
) -> str:
    """Create prompt for documentation generation"""
    
    prompt = f"""Generate comprehensive documentation for the following code change:

## Change Information
- Commit: {change_report['commit_sha']}
- Author: {change_report['author']}
- Message: {change_report['message']}
- Type: {change_report['change_type']}

## Files Changed
"""
    
    for file_change in change_report['files_changed']:
        prompt += f"\n### {file_change['path']}\n"
        prompt += f"- Change Type: {file_change['change_type']}\n"
        prompt += f"- Language: {file_change['language']}\n"
        
        if file_change.get('symbols_added'):
            prompt += f"- Added: {', '.join([s['name'] for s in file_change['symbols_added']])}\n"
        if file_change.get('symbols_modified'):
            prompt += f"- Modified: {', '.join([s['name'] for s in file_change['symbols_modified']])}\n"
        if file_change.get('symbols_removed'):
            prompt += f"- Removed: {', '.join([s['name'] for s in file_change['symbols_removed']])}\n"
    
    if context:
        prompt += f"\n## Architectural Context\n{context}\n"
    
    if related_code:
        prompt += "\n## Related Code\n"
        for code in related_code[:3]:  # Limit to top 3
            prompt += f"- {code['file_path']}: {code['description']}\n"
    
    prompt += """

## Task
Generate documentation that includes:

1. **Overview**: Brief description of what changed and why
2. **Changes Made**: Detailed list of modifications
3. **Architecture Context**: How this fits into the larger system
4. **Dependencies**: What this code depends on and what depends on it
5. **Usage Examples**: Practical code examples showing how to use the changes
6. **Edge Cases**: Important considerations and potential gotchas
7. **Performance**: Any performance implications (if relevant)
8. **Security**: Security considerations (if applicable)

Use clear markdown formatting with proper headings, code blocks, and bullet points.
"""
    
    return prompt


QUERY_SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions about codebases and their documentation.

Guidelines:
1. Provide accurate, specific answers
2. Cite sources with file paths and line numbers
3. Include relevant code snippets
4. Explain concepts clearly
5. Suggest related topics when helpful
6. Admit when you don't know something

Always structure your answers with:
- Direct answer to the question
- Supporting evidence from code/docs
- Relevant examples
- Related information (if applicable)
"""


def create_query_prompt(
    question: str,
    context_chunks: list,
    conversation_history: list = None
) -> str:
    """Create prompt for query answering"""
    
    prompt = "Answer the following question based on the provided context:\n\n"
    
    if conversation_history:
        prompt += "## Conversation History\n"
        for msg in conversation_history[-3:]:  # Last 3 messages
            prompt += f"- {msg['role']}: {msg['content']}\n"
        prompt += "\n"
    
    prompt += f"## Question\n{question}\n\n"
    
    prompt += "## Context\n"
    for i, chunk in enumerate(context_chunks, 1):
        prompt += f"\n### Source {i}: {chunk['source']}\n"
        prompt += f"```{chunk.get('language', '')}\n{chunk['content']}\n```\n"
    
    prompt += """

## Instructions
Provide a comprehensive answer that:
1. Directly addresses the question
2. References specific sources (use "Source N" format)
3. Includes relevant code examples
4. Explains any complex concepts
5. Suggests related topics if helpful

Format your response in markdown.
"""
    
    return prompt
```

## Alternative: Free LLM Providers

If Ollama Cloud has limitations, consider these free alternatives:

### 1. Groq (Recommended)
- **Free Tier**: 14,400 requests/day
- **Models**: Llama 3, Mixtral
- **Speed**: Very fast inference
- **Setup**: Similar to OpenAI API

```python
# Use with OpenAI-compatible client
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
```

### 2. Together AI
- **Free Tier**: $25 credit
- **Models**: Many open-source models
- **Setup**: OpenAI-compatible

### 3. HuggingFace Inference API
- **Free Tier**: Rate-limited but free
- **Models**: Thousands of models
- **Setup**: Different API format

### 4. Local Ollama (Development)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.1:8b

# Run server
ollama serve
```

## Cost Optimization Strategies

### 1. Response Caching
```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_llm_response(ttl=86400):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"llm:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return cached.decode()
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, result)
            return result
        return wrapper
    return decorator
```

### 2. Request Batching
```python
class BatchProcessor:
    def __init__(self, batch_size=10, wait_time=5):
        self.batch_size = batch_size
        self.wait_time = wait_time
        self.queue = []
    
    async def add_request(self, request):
        self.queue.append(request)
        if len(self.queue) >= self.batch_size:
            await self.process_batch()
    
    async def process_batch(self):
        # Process multiple requests in one API call
        batch = self.queue[:self.batch_size]
        self.queue = self.queue[self.batch_size:]
        # ... process batch
```

### 3. Model Selection
```python
def select_model(task_complexity: str) -> str:
    """Select appropriate model based on task"""
    if task_complexity == "simple":
        return "llama3.1:8b"  # Faster, cheaper
    elif task_complexity == "medium":
        return "llama3.1:13b"
    else:
        return "llama3.1:70b"  # Most capable
```

### 4. Token Optimization
```python
def optimize_prompt(prompt: str, max_tokens: int = 2000) -> str:
    """Reduce prompt size while preserving meaning"""
    # Remove unnecessary whitespace
    prompt = " ".join(prompt.split())
    
    # Truncate if too long
    words = prompt.split()
    if len(words) > max_tokens:
        prompt = " ".join(words[:max_tokens]) + "..."
    
    return prompt
```

## Monitoring and Alerts

```python
import structlog

logger = structlog.get_logger()

class LLMMonitor:
    def __init__(self):
        self.daily_requests = 0
        self.daily_tokens = 0
        self.errors = 0
    
    def log_request(self, tokens: int, success: bool):
        self.daily_requests += 1
        self.daily_tokens += tokens
        
        if not success:
            self.errors += 1
        
        # Alert if approaching limits
        if self.daily_tokens > 40000:  # 80% of 50K limit
            logger.warning(
                "Approaching daily token limit",
                tokens_used=self.daily_tokens,
                limit=50000
            )
        
        if self.errors > 10:
            logger.error(
                "High error rate detected",
                errors=self.errors,
                requests=self.daily_requests
            )
```

## Testing

```python
import pytest
from app.services.llm import llm_service

@pytest.mark.asyncio
async def test_llm_generation():
    """Test basic LLM generation"""
    response = await llm_service.generate(
        prompt="Explain what a REST API is in one sentence.",
        max_tokens=100
    )
    assert len(response) > 0
    assert "API" in response

@pytest.mark.asyncio
async def test_llm_structured_output():
    """Test structured JSON output"""
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "key_points": {"type": "array"}
        }
    }
    
    response = await llm_service.generate_structured(
        prompt="Summarize the benefits of using Docker",
        schema=schema
    )
    
    assert "summary" in response
    assert "key_points" in response
    assert isinstance(response["key_points"], list)
```

## Conclusion

This integration guide provides a flexible approach to using Ollama Cloud with fallbacks and optimizations for free-tier usage. The system is designed to work with multiple LLM providers, making it easy to switch or use hybrid approaches based on availability and cost.