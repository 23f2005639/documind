"""
Writer Agent for DocuMind
Generates documentation from code changes using LLM and context retrieval
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
import structlog

from app.models.change_report import ChangeReport
from app.models.documentation import DocumentationPage, DocumentationCreate
from app.services.llm import llm_service, DOCUMENTATION_SYSTEM_PROMPT
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.services.notion import notion_service
from app.db.database import supabase

logger = structlog.get_logger()


class WriterAgent:
    """
    Agent responsible for generating documentation from code changes
    
    Workflow:
    1. Receive change report
    2. Retrieve relevant context from vector store
    3. Generate documentation using LLM
    4. Format for Notion
    5. Create/update Notion page
    6. Store metadata in database
    """
    
    def __init__(self):
        self.max_context_tokens = 4000
        self.min_similarity_score = 0.7
        
        logger.info("Writer Agent initialized")
    
    async def generate_documentation(
        self,
        change_report: ChangeReport,
        repository_id: UUID
    ) -> DocumentationPage:
        """
        Generate documentation for a change report
        
        Args:
            change_report: Parsed change report
            repository_id: Repository UUID
            
        Returns:
            Created documentation page
        """
        logger.info(
            "Generating documentation",
            commit_sha=change_report.commit_sha,
            repository_id=str(repository_id)
        )
        
        # Step 1: Retrieve relevant context
        context = await self._retrieve_context(change_report, repository_id)
        
        # Step 2: Generate documentation content
        doc_content = await self._generate_content(change_report, context)
        
        # Step 3: Format for Notion
        notion_blocks = self._format_for_notion(change_report, doc_content)
        
        # Step 4: Create Notion page
        notion_page = await notion_service.create_page(
            title=f"Documentation: {change_report.commit_sha[:7]} - {change_report.message[:50]}",
            blocks=notion_blocks,
            properties={
                "Type": {"select": {"name": change_report.change_type.value}},
                "Commit": {"rich_text": [{"text": {"content": change_report.commit_sha}}]},
                "Author": {"rich_text": [{"text": {"content": change_report.author}}]}
            }
        )
        
        # Step 5: Store in database
        doc_page = await self._store_documentation(
            repository_id=repository_id,
            notion_page_id=notion_page["id"],
            title=f"Documentation: {change_report.commit_sha[:7]}",
            content=doc_content["summary"],
            change_report=change_report
        )
        
        # Step 6: Create code-doc mappings
        await self._create_code_mappings(doc_page.id, change_report)
        
        # Step 7: Index in vector store
        await self._index_documentation(doc_page, doc_content)
        
        logger.info(
            "Documentation generated successfully",
            doc_id=str(doc_page.id),
            notion_page_id=notion_page["id"]
        )
        
        return doc_page
    
    async def _retrieve_context(
        self,
        change_report: ChangeReport,
        repository_id: UUID
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context for documentation generation
        
        Args:
            change_report: Change report
            repository_id: Repository ID
            
        Returns:
            Context dictionary with related code and docs
        """
        # Build search query from change report
        query_parts = [
            change_report.message,
            *[f.file_path for f in change_report.files_changed[:5]]
        ]
        query = " ".join(query_parts)
        
        # Search vector store for relevant context
        results = await vector_store.search(
            query=query,
            limit=10,
            filters={"repository_id": str(repository_id)},
            score_threshold=self.min_similarity_score
        )
        
        # Organize context
        context = {
            "related_docs": [],
            "related_code": [],
            "similar_changes": []
        }
        
        for result in results:
            metadata = result.get("metadata", {})
            doc_type = metadata.get("type", "unknown")
            
            if doc_type == "documentation":
                context["related_docs"].append({
                    "content": result["content"],
                    "score": result["score"]
                })
            elif doc_type == "code":
                context["related_code"].append({
                    "file_path": metadata.get("file_path"),
                    "content": result["content"],
                    "score": result["score"]
                })
        
        logger.info(
            "Context retrieved",
            related_docs=len(context["related_docs"]),
            related_code=len(context["related_code"])
        )
        
        return context
    
    async def _generate_content(
        self,
        change_report: ChangeReport,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate documentation content using LLM
        
        Args:
            change_report: Change report
            context: Retrieved context
            
        Returns:
            Generated documentation content
        """
        # Build prompt
        prompt = self._build_documentation_prompt(change_report, context)
        
        # Generate with LLM
        response = await llm_service.generate(
            prompt=prompt,
            system_prompt=DOCUMENTATION_SYSTEM_PROMPT,
            max_tokens=2000,
            temperature=0.7
        )
        
        # Parse response into structured format
        content = self._parse_llm_response(response)
        
        return content
    
    def _build_documentation_prompt(
        self,
        change_report: ChangeReport,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for documentation generation"""
        
        # Format files changed
        files_summary = "\n".join([
            f"- {f.file_path} ({f.change_type.value}): {f.additions} additions, {f.deletions} deletions"
            for f in change_report.files_changed[:10]
        ])
        
        # Format context
        context_summary = ""
        if context["related_docs"]:
            context_summary += "\n\nRelated Documentation:\n"
            for doc in context["related_docs"][:3]:
                context_summary += f"- {doc['content'][:200]}...\n"
        
        if context["related_code"]:
            context_summary += "\n\nRelated Code:\n"
            for code in context["related_code"][:3]:
                context_summary += f"- {code['file_path']}: {code['content'][:200]}...\n"
        
        prompt = f"""Generate comprehensive documentation for the following code change:

**Commit Information:**
- SHA: {change_report.commit_sha}
- Author: {change_report.author}
- Message: {change_report.message}
- Type: {change_report.change_type.value}
- Impact Score: {change_report.impact_score}

**Files Changed:**
{files_summary}

**Context:**
{context_summary}

Please generate documentation that includes:
1. A clear summary (2-3 sentences)
2. Detailed explanation of changes
3. Impact on the codebase
4. Usage examples (if applicable)
5. Breaking changes (if any)
6. Related files and dependencies

Format the response as follows:
SUMMARY: [summary text]
DETAILS: [detailed explanation]
IMPACT: [impact description]
EXAMPLES: [code examples if applicable]
BREAKING: [breaking changes if any]
RELATED: [related files]
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        
        sections = {
            "summary": "",
            "details": "",
            "impact": "",
            "examples": "",
            "breaking": "",
            "related": ""
        }
        
        current_section = None
        lines = response.split("\n")
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("SUMMARY:"):
                current_section = "summary"
                sections["summary"] = line.replace("SUMMARY:", "").strip()
            elif line.startswith("DETAILS:"):
                current_section = "details"
                sections["details"] = line.replace("DETAILS:", "").strip()
            elif line.startswith("IMPACT:"):
                current_section = "impact"
                sections["impact"] = line.replace("IMPACT:", "").strip()
            elif line.startswith("EXAMPLES:"):
                current_section = "examples"
                sections["examples"] = line.replace("EXAMPLES:", "").strip()
            elif line.startswith("BREAKING:"):
                current_section = "breaking"
                sections["breaking"] = line.replace("BREAKING:", "").strip()
            elif line.startswith("RELATED:"):
                current_section = "related"
                sections["related"] = line.replace("RELATED:", "").strip()
            elif current_section and line:
                sections[current_section] += "\n" + line
        
        return sections
    
    def _format_for_notion(
        self,
        change_report: ChangeReport,
        content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Format documentation content as Notion blocks"""
        
        # Extract code examples
        code_examples = []
        if content.get("examples"):
            # Simple extraction - in production, use better parsing
            code_examples.append({
                "code": content["examples"],
                "language": "python"
            })
        
        # Extract related files
        related_files = [f.file_path for f in change_report.files_changed]
        
        # Format changes
        changes = [
            {
                "type": change_report.change_type.value,
                "description": content.get("details", "")
            }
        ]
        
        # Add breaking changes if any
        if content.get("breaking"):
            changes.append({
                "type": "BREAKING",
                "description": content["breaking"]
            })
        
        return notion_service.format_documentation(
            title=f"Documentation: {change_report.commit_sha[:7]}",
            summary=content.get("summary", ""),
            changes=changes,
            code_examples=code_examples,
            related_files=related_files
        )
    
    async def _store_documentation(
        self,
        repository_id: UUID,
        notion_page_id: str,
        title: str,
        content: str,
        change_report: ChangeReport
    ) -> DocumentationPage:
        """Store documentation metadata in database"""
        
        # Insert into database
        result = supabase.table("documentation_pages").insert({
            "repository_id": str(repository_id),
            "notion_page_id": notion_page_id,
            "title": title,
            "content": content,
            "version": 1,
            "is_stale": False,
            "tags": [change_report.change_type.value]
        }).execute()
        
        doc_data = result.data[0]
        
        return DocumentationPage(
            id=UUID(doc_data["id"]),
            repository_id=repository_id,
            notion_page_id=notion_page_id,
            title=title,
            content=content,
            version=1,
            is_stale=False,
            tags=[change_report.change_type.value]
        )
    
    async def _create_code_mappings(
        self,
        doc_id: UUID,
        change_report: ChangeReport
    ):
        """Create code-to-documentation mappings"""
        
        mappings = []
        for file_change in change_report.files_changed:
            for symbol in file_change.symbols:
                mappings.append({
                    "documentation_page_id": str(doc_id),
                    "file_path": file_change.file_path,
                    "line_start": symbol.line_start,
                    "line_end": symbol.line_end,
                    "symbol_name": symbol.name,
                    "symbol_type": symbol.type.value,
                    "commit_sha": change_report.commit_sha
                })
        
        if mappings:
            supabase.table("code_doc_mappings").insert(mappings).execute()
            logger.info("Code mappings created", count=len(mappings))
    
    async def _index_documentation(
        self,
        doc_page: DocumentationPage,
        content: Dict[str, Any]
    ):
        """Index documentation in vector store"""
        
        # Combine content for indexing
        full_content = f"{doc_page.title}\n\n{content.get('summary', '')}\n\n{content.get('details', '')}"
        
        await vector_store.index_document(
            doc_id=str(doc_page.id),
            content=full_content,
            metadata={
                "type": "documentation",
                "repository_id": str(doc_page.repository_id),
                "notion_page_id": doc_page.notion_page_id,
                "title": doc_page.title,
                "tags": doc_page.tags
            }
        )
        
        logger.info("Documentation indexed in vector store", doc_id=str(doc_page.id))


# Global instance
writer_agent = WriterAgent()

# Made with Bob
