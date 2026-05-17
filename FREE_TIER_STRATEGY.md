# Free Tier Strategy for DocuMind

## Overview

This document outlines the complete strategy for building and running DocuMind using only free-tier services, ensuring zero operational costs while maintaining production-grade functionality.

## Service Selection & Limits

### 1. LLM Provider: Groq (Primary) + Ollama Local (Fallback)

**Why Groq over Ollama Cloud**:
- Groq offers 14,400 free requests/day (vs Ollama Cloud's uncertain limits)
- Extremely fast inference (up to 10x faster than other providers)
- OpenAI-compatible API (easy integration)
- Proven free tier availability

**Groq Free Tier**:
- **Requests**: 14,400/day (~600/hour)
- **Rate Limit**: 30 requests/minute
- **Models**: Llama 3.1 (8B, 70B), Mixtral 8x7B, Gemma 7B
- **Context**: Up to 8K tokens
- **Cost**: $0

**Local Ollama Fallback**:
- Use when Groq limits are reached
- Development and testing
- Offline capability
- Models: Llama 3.1, Mistral, CodeLlama

**Implementation**:
```python
# Priority order: Groq -> Local Ollama
LLM_PROVIDERS = [
    {"name": "groq", "url": "https://api.groq.com/openai/v1", "priority": 1},
    {"name": "ollama", "url": "http://localhost:11434", "priority": 2}
]
```

### 2. Vector Database: Qdrant Cloud (Primary) + ChromaDB (Fallback)

**Why Qdrant over Pinecone**:
- Qdrant Cloud offers 1GB free cluster (vs Pinecone's 1 index limit)
- Better performance for smaller datasets
- More flexible filtering
- Open-source with local option

**Qdrant Cloud Free Tier**:
- **Storage**: 1GB (~2.5M vectors at 384 dimensions)
- **Clusters**: 1 free cluster
- **API Calls**: Unlimited
- **Performance**: Fast enough for production
- **Cost**: $0

**ChromaDB Local Fallback**:
- Embedded database (no server needed)
- Perfect for development
- Easy migration to Qdrant
- Persistent storage

**Implementation**:
```python
# Use Qdrant Cloud for production, ChromaDB for dev
if settings.app_env == "production":
    vector_store = QdrantVectorStore()
else:
    vector_store = ChromaDBVectorStore()
```

### 3. Database: Supabase PostgreSQL

**Supabase Free Tier**:
- **Database**: 500MB storage
- **Bandwidth**: 2GB/month
- **API Requests**: Unlimited
- **Features**: pgvector, real-time, auth
- **Backups**: Daily (7 days retention)
- **Cost**: $0

**Optimization Strategies**:
- Store large content in Notion/files, not database
- Use efficient indexing
- Implement data archival (move old data to cold storage)
- Compress JSON fields
- Use database views for complex queries

**Storage Breakdown** (for 10 repositories):
```
- Repositories: ~10KB
- Documentation pages: ~50MB (metadata only)
- Code mappings: ~20MB
- Change reports: ~30MB
- Query history: ~10MB
- Embeddings: Store in Qdrant, not PostgreSQL
Total: ~110MB (well under 500MB limit)
```

### 4. Documentation Platform: Notion

**Notion Free Tier**:
- **Pages**: Unlimited
- **Blocks**: Unlimited
- **API Calls**: 3 requests/second
- **File Uploads**: 5MB per file
- **Integrations**: Unlimited
- **Cost**: $0

**Optimization**:
- Batch updates where possible
- Implement rate limiting (3 req/sec)
- Use exponential backoff
- Cache Notion content locally
- Markdown fallback for version control

### 5. Hosting: Railway (Primary) + Render (Alternative)

**Railway Free Tier**:
- **Hours**: 500 hours/month (enough for 1 service 24/7)
- **Memory**: 512MB RAM
- **CPU**: Shared
- **Deployments**: Unlimited
- **Custom Domain**: Yes
- **Cost**: $0

**Render Free Tier** (Alternative):
- **Services**: Multiple free services
- **Memory**: 512MB RAM
- **Spin Down**: After 15 min inactivity
- **Build Minutes**: 500/month
- **Cost**: $0

**Deployment Strategy**:
- Backend on Railway (always-on)
- Frontend on Vercel/Netlify (free static hosting)
- Database on Supabase (managed)
- Vector DB on Qdrant Cloud (managed)

### 6. Frontend Hosting: Vercel

**Vercel Free Tier**:
- **Bandwidth**: 100GB/month
- **Builds**: Unlimited
- **Deployments**: Unlimited
- **Custom Domain**: Yes
- **Edge Functions**: 100GB-hours
- **Cost**: $0

### 7. GitHub

**GitHub Free Tier**:
- **Repositories**: Unlimited public/private
- **Webhooks**: Unlimited
- **API Calls**: 5,000/hour (authenticated)
- **Actions**: 2,000 minutes/month
- **Storage**: 500MB packages
- **Cost**: $0

### 8. Additional Free Services

**Redis (Upstash)**:
- **Storage**: 256MB
- **Commands**: 10K/day
- **Use**: LLM response caching
- **Cost**: $0

**Monitoring (Better Stack)**:
- **Logs**: 1GB/month
- **Uptime Checks**: 10 monitors
- **Incidents**: Unlimited
- **Cost**: $0

## Architecture for Free Tier

```
┌─────────────────────────────────────────────────────────────┐
│                     Free Tier Stack                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (Vercel)                                           │
│  ├─ React App                                                │
│  ├─ Static Assets                                            │
│  └─ Edge Functions                                           │
│                                                               │
│  Backend (Railway)                                           │
│  ├─ FastAPI Application                                      │
│  ├─ Agent Workers                                            │
│  └─ Background Tasks                                         │
│                                                               │
│  LLM (Groq Cloud)                                            │
│  ├─ Primary: Groq API                                        │
│  └─ Fallback: Local Ollama                                   │
│                                                               │
│  Vector DB (Qdrant Cloud)                                    │
│  ├─ Code Embeddings                                          │
│  ├─ Doc Embeddings                                           │
│  └─ Semantic Search                                          │
│                                                               │
│  Database (Supabase)                                         │
│  ├─ PostgreSQL + pgvector                                    │
│  ├─ Metadata Storage                                         │
│  └─ Real-time Subscriptions                                  │
│                                                               │
│  Cache (Upstash Redis)                                       │
│  ├─ LLM Response Cache                                       │
│  ├─ API Response Cache                                       │
│  └─ Rate Limit Tracking                                      │
│                                                               │
│  Documentation (Notion)                                      │
│  ├─ Generated Docs                                           │
│  ├─ Rich Formatting                                          │
│  └─ Collaboration                                            │
│                                                               │
│  Source Control (GitHub)                                     │
│  ├─ Code Repository                                          │
│  ├─ Webhooks                                                 │
│  └─ CI/CD (Actions)                                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Cost Optimization Techniques

### 1. Request Batching

```python
class RequestBatcher:
    """Batch multiple requests to reduce API calls"""
    
    def __init__(self, batch_size=10, max_wait=5):
        self.batch_size = batch_size
        self.max_wait = max_wait
        self.queue = []
        self.timer = None
    
    async def add(self, request):
        self.queue.append(request)
        
        if len(self.queue) >= self.batch_size:
            await self.flush()
        elif not self.timer:
            self.timer = asyncio.create_task(self._wait_and_flush())
    
    async def _wait_and_flush(self):
        await asyncio.sleep(self.max_wait)
        await self.flush()
    
    async def flush(self):
        if not self.queue:
            return
        
        batch = self.queue[:self.batch_size]
        self.queue = self.queue[self.batch_size:]
        
        # Process batch in single API call
        await self.process_batch(batch)
        
        if self.timer:
            self.timer.cancel()
            self.timer = None
```

### 2. Intelligent Caching

```python
class SmartCache:
    """Multi-layer caching strategy"""
    
    def __init__(self):
        self.memory_cache = {}  # In-memory (fast)
        self.redis_cache = redis.Redis()  # Distributed (persistent)
    
    async def get(self, key: str):
        # Try memory first
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Try Redis
        value = self.redis_cache.get(key)
        if value:
            self.memory_cache[key] = value  # Populate memory
            return value
        
        return None
    
    async def set(self, key: str, value: any, ttl: int = 3600):
        # Set in both layers
        self.memory_cache[key] = value
        self.redis_cache.setex(key, ttl, value)
```

### 3. Lazy Loading

```python
class LazyEmbedding:
    """Generate embeddings only when needed"""
    
    def __init__(self):
        self.embedding_cache = {}
    
    async def get_embedding(self, text: str):
        # Check if already embedded
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
        
        # Generate only if not cached
        embedding = await self.generate_embedding(text)
        self.embedding_cache[text_hash] = embedding
        
        return embedding
```

### 4. Incremental Processing

```python
class IncrementalProcessor:
    """Process only what changed"""
    
    async def process_changes(self, commit_sha: str):
        # Get previous commit
        prev_commit = await self.get_previous_commit(commit_sha)
        
        # Get diff only
        diff = await self.get_diff(prev_commit, commit_sha)
        
        # Process only changed files
        for file_change in diff:
            if file_change.type == "modified":
                # Update only changed sections
                await self.update_documentation_section(file_change)
            elif file_change.type == "added":
                # Generate new documentation
                await self.generate_documentation(file_change)
            # Skip deleted files
```

### 5. Smart Rate Limiting

```python
class AdaptiveRateLimiter:
    """Adjust rate based on usage"""
    
    def __init__(self):
        self.daily_limit = 14400  # Groq limit
        self.used_today = 0
        self.current_rate = 30  # requests/minute
    
    async def acquire(self):
        # Check daily limit
        if self.used_today >= self.daily_limit * 0.9:  # 90% threshold
            # Slow down
            self.current_rate = 10
        
        # Wait if needed
        await self.wait_for_slot()
        
        self.used_today += 1
    
    async def wait_for_slot(self):
        # Implement token bucket algorithm
        pass
```

## Monitoring Free Tier Usage

### Dashboard Metrics

```python
class UsageMonitor:
    """Track usage across all services"""
    
    async def get_usage_stats(self):
        return {
            "groq": {
                "requests_today": self.groq_requests,
                "limit": 14400,
                "percentage": (self.groq_requests / 14400) * 100
            },
            "qdrant": {
                "vectors_stored": await self.get_vector_count(),
                "limit": 2500000,
                "storage_mb": await self.get_storage_size()
            },
            "supabase": {
                "storage_mb": await self.get_db_size(),
                "limit_mb": 500,
                "bandwidth_mb": await self.get_bandwidth()
            },
            "notion": {
                "requests_today": self.notion_requests,
                "rate_limit": "3/sec"
            },
            "railway": {
                "hours_used": await self.get_railway_hours(),
                "limit": 500
            }
        }
```

### Alerts

```python
class UsageAlerts:
    """Alert when approaching limits"""
    
    async def check_limits(self):
        stats = await self.monitor.get_usage_stats()
        
        # Alert at 80% usage
        for service, data in stats.items():
            if "percentage" in data and data["percentage"] > 80:
                await self.send_alert(
                    f"⚠️ {service} usage at {data['percentage']:.1f}%"
                )
```

## Scaling Strategy

### When to Upgrade

**Groq → Paid LLM**:
- Exceeding 14,400 requests/day consistently
- Need for larger context windows (>8K tokens)
- Require specific models not available on Groq

**Qdrant Cloud → Paid Tier**:
- Exceeding 1GB storage (~2.5M vectors)
- Need for multiple clusters
- Require higher performance

**Supabase → Paid Tier**:
- Exceeding 500MB database storage
- Need for more than 2GB bandwidth/month
- Require point-in-time recovery

**Railway → Paid Tier**:
- Need more than 512MB RAM
- Require dedicated CPU
- Need multiple services running 24/7

### Hybrid Approach

```python
class HybridProvider:
    """Use free tier until limits, then switch to paid"""
    
    def __init__(self):
        self.free_provider = GroqProvider()
        self.paid_provider = OpenAIProvider()  # Fallback
        self.use_paid = False
    
    async def generate(self, prompt: str):
        if not self.use_paid:
            try:
                return await self.free_provider.generate(prompt)
            except RateLimitError:
                logger.warning("Free tier limit reached, switching to paid")
                self.use_paid = True
        
        return await self.paid_provider.generate(prompt)
```

## Cost Projection

### Free Tier Capacity

**Repositories**: 10-20 active repositories
**Documentation Pages**: 1,000-2,000 pages
**Queries**: 500-1,000 per day
**Users**: 10-50 concurrent users
**Uptime**: 24/7 with 99% availability

### When Costs Begin

**Estimated Monthly Costs** (if exceeding free tiers):

```
Groq/OpenAI:        $0-50   (if >14K requests/day)
Qdrant:             $0-25   (if >1GB vectors)
Supabase:           $0-25   (if >500MB DB)
Railway:            $0-20   (if >512MB RAM)
Redis:              $0-10   (if >256MB cache)
Total:              $0-130/month
```

**Break-even Point**: ~50 active users or 20+ repositories

## Implementation Checklist

- [ ] Set up Groq account and API key
- [ ] Create Qdrant Cloud cluster
- [ ] Initialize Supabase project
- [ ] Configure Notion integration
- [ ] Set up Railway deployment
- [ ] Deploy frontend to Vercel
- [ ] Configure GitHub webhooks
- [ ] Set up Upstash Redis
- [ ] Implement caching layer
- [ ] Add usage monitoring
- [ ] Configure rate limiting
- [ ] Set up alerts
- [ ] Test fallback mechanisms
- [ ] Document scaling procedures

## Conclusion

This free-tier strategy provides a production-ready system with:

✅ **Zero operational costs** for small to medium usage
✅ **Scalable architecture** that grows with demand
✅ **Fallback mechanisms** for reliability
✅ **Clear upgrade path** when needed
✅ **Professional features** despite being free

The system can handle 10-20 repositories with 500+ queries per day completely free, making it ideal for startups, open-source projects, and small teams.