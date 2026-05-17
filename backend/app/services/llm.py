"""
LLM Service for DocuMind using Ollama Cloud
Handles text generation with caching and rate limiting
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
import time
import hashlib
import json
from datetime import datetime, timedelta
import asyncio
import structlog
import httpx

from app.config import settings

logger = structlog.get_logger()


# System prompts for different use cases
DOCUMENTATION_SYSTEM_PROMPT = """You are a technical documentation expert. Your task is to generate clear, comprehensive documentation for code changes.

Guidelines:
- Write in clear, professional language
- Include code examples where relevant
- Explain the "why" behind changes, not just the "what"
- Structure documentation with clear sections
- Use markdown formatting
- Be concise but thorough"""

QUERY_SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions about codebases. Your task is to provide accurate, helpful answers based on the provided context.

Guidelines:
- Answer based only on the provided context
- Be clear and concise
- Cite specific sources when possible
- If you're unsure, say so
- Provide code examples when helpful
- Use markdown formatting"""

SUMMARY_SYSTEM_PROMPT = """You are a technical writer specializing in change summaries. Your task is to create clear, concise summaries of code changes.

Guidelines:
- Focus on the impact and purpose of changes
- Use bullet points for clarity
- Highlight breaking changes
- Keep it brief but informative
- Use technical but accessible language"""


class LLMService:
    """Service for LLM text generation with Ollama Cloud"""

    DOCUMENTATION_SYSTEM_PROMPT = DOCUMENTATION_SYSTEM_PROMPT
    QUERY_SYSTEM_PROMPT = QUERY_SYSTEM_PROMPT
    SUMMARY_SYSTEM_PROMPT = SUMMARY_SYSTEM_PROMPT

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.api_key = settings.ollama_api_key
        self.model = settings.ollama_model
        
        # Rate limiting
        self.rate_limit_per_minute = settings.rate_limit_per_minute
        self.rate_limit_per_day = 14400  # Ollama Cloud free tier
        self.request_times: List[float] = []
        self.daily_requests = 0
        self.daily_reset_time = datetime.now() + timedelta(days=1)
        
        # Caching
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 24 * 60 * 60  # 24 hours
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info(
            "LLM Service initialized",
            model=self.model,
            base_url=self.base_url
        )
    
    def _get_cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters"""
        key_data = {
            "prompt": prompt,
            **kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[str]:
        """Check if response is in cache and still valid"""
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                logger.info("Cache hit", cache_key=cache_key[:8])
                return cached['response']
            else:
                # Expired
                del self.cache[cache_key]
        return None
    
    def _store_cache(self, cache_key: str, response: str):
        """Store response in cache"""
        self.cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
        logger.debug("Cached response", cache_key=cache_key[:8])
    
    async def _check_rate_limit(self):
        """Check and enforce rate limits"""
        now = time.time()
        
        # Reset daily counter if needed
        if datetime.now() > self.daily_reset_time:
            self.daily_requests = 0
            self.daily_reset_time = datetime.now() + timedelta(days=1)
            logger.info("Daily rate limit reset")
        
        # Check daily limit
        if self.daily_requests >= self.rate_limit_per_day:
            raise Exception("Daily rate limit exceeded")
        
        # Check per-minute limit
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.rate_limit_per_minute:
            wait_time = 60 - (now - self.request_times[0])
            logger.warning("Rate limit reached, waiting", wait_seconds=wait_time)
            await asyncio.sleep(wait_time)
        
        self.request_times.append(now)
        self.daily_requests += 1
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = QUERY_SYSTEM_PROMPT,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        use_cache: bool = True
    ) -> str:
        """
        Generate text using LLM
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_cache: Whether to use caching
            
        Returns:
            Generated text
        """
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            cached_response = self._check_cache(cache_key)
            if cached_response:
                return cached_response
        
        # Check rate limit
        await self._check_rate_limit()
        
        # Prepare request — native Ollama Cloud /api/chat format
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }

        # Make request with retries
        for attempt in range(3):
            try:
                logger.info(
                    "Generating text",
                    attempt=attempt + 1,
                    prompt_length=len(prompt)
                )

                response = await self.client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()

                result = response.json()
                generated_text = result['message']['content']
                
                # Cache response
                if use_cache:
                    self._store_cache(cache_key, generated_text)
                
                logger.info(
                    "Text generated successfully",
                    response_length=len(generated_text)
                )
                
                return generated_text
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    "HTTP error",
                    status_code=e.response.status_code,
                    attempt=attempt + 1
                )
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                logger.error("Generation failed", error=str(e), attempt=attempt + 1)
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = QUERY_SYSTEM_PROMPT,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Generate text with streaming
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Yields:
            Text chunks as they are generated
        """
        # Check rate limit
        await self._check_rate_limit()
        
        # Prepare request — native Ollama Cloud /api/chat streaming format
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }

        logger.info("Starting streaming generation", prompt_length=len(prompt))

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get('message', {}).get('content', '')
                        if content:
                            yield content
                        if chunk.get('done'):
                            break
                    except json.JSONDecodeError:
                        continue
            
            logger.info("Streaming generation completed")
            
        except Exception as e:
            logger.error("Streaming generation failed", error=str(e))
            raise
    
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = QUERY_SYSTEM_PROMPT,
        response_format: Dict[str, Any] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            response_format: Expected response format
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Parsed JSON response
        """
        # Add JSON instruction to prompt
        json_prompt = f"{prompt}\n\nRespond with valid JSON only."
        
        # Generate text
        response_text = await self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            use_cache=False  # Don't cache structured responses
        )
        
        # Parse JSON
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            result = json.loads(response_text)
            logger.info("Structured response parsed successfully")
            return result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e))
            # Return a fallback structure
            return {"error": "Failed to parse response", "raw": response_text}
    
    async def batch_generate(
        self,
        prompts: List[str],
        system_prompt: str = QUERY_SYSTEM_PROMPT,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> List[str]:
        """
        Generate text for multiple prompts in parallel
        
        Args:
            prompts: List of prompts
            system_prompt: System prompt
            max_tokens: Maximum tokens per generation
            temperature: Sampling temperature
            
        Returns:
            List of generated texts
        """
        logger.info("Starting batch generation", count=len(prompts))
        
        tasks = [
            self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            for prompt in prompts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Batch generation failed", index=i, error=str(result))
                processed_results.append(f"Error: {str(result)}")
            else:
                processed_results.append(result)
        
        logger.info("Batch generation completed", count=len(processed_results))
        
        return processed_results
    
    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = time.time()
        valid_entries = sum(
            1 for cached in self.cache.values()
            if now - cached['timestamp'] < self.cache_ttl
        )
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "cache_ttl_seconds": self.cache_ttl,
            "daily_requests": self.daily_requests,
            "daily_limit": self.rate_limit_per_day,
            "requests_remaining": self.rate_limit_per_day - self.daily_requests
        }


# Global instance
llm_service = LLMService()

# Made with Bob