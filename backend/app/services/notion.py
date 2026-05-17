"""
Notion Service for DocuMind
Manages documentation storage and formatting in Notion
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from notion_client import AsyncClient
from notion_client.errors import APIResponseError

from app.config import settings

logger = structlog.get_logger()


class NotionService:
    """Service for interacting with Notion API"""
    
    def __init__(self):
        self.client = AsyncClient(auth=settings.notion_api_key)
        self.database_id = settings.notion_database_id
        self.rate_limit = settings.notion_rate_limit  # requests per second
        self.last_request_time = datetime.now()
        
        logger.info("Notion service initialized", database_id=self.database_id[:8])
    
    async def _rate_limit(self):
        """Implement rate limiting (3 requests per second)"""
        now = datetime.now()
        time_since_last = (now - self.last_request_time).total_seconds()
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = datetime.now()
    
    def _format_rich_text(self, text: str) -> List[Dict[str, Any]]:
        """Format text as Notion rich text"""
        return [{"type": "text", "text": {"content": text}}]
    
    def _create_heading_block(self, text: str, level: int = 2) -> Dict[str, Any]:
        """Create a heading block"""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": self._format_rich_text(text)
            }
        }
    
    def _create_paragraph_block(self, text: str) -> Dict[str, Any]:
        """Create a paragraph block"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": self._format_rich_text(text)
            }
        }
    
    def _create_code_block(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Create a code block"""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": self._format_rich_text(code),
                "language": language
            }
        }
    
    def _create_bulleted_list_block(self, text: str) -> Dict[str, Any]:
        """Create a bulleted list item"""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": self._format_rich_text(text)
            }
        }
    
    def _create_callout_block(self, text: str, emoji: str = "💡") -> Dict[str, Any]:
        """Create a callout block"""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": self._format_rich_text(text),
                "icon": {"type": "emoji", "emoji": emoji}
            }
        }
    
    def _create_divider_block(self) -> Dict[str, Any]:
        """Create a divider block"""
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    
    async def create_page(
        self,
        title: str,
        blocks: List[Dict[str, Any]],
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new page in the Notion database
        
        Args:
            title: Page title
            blocks: List of content blocks
            properties: Additional page properties
            
        Returns:
            Created page object
        """
        await self._rate_limit()
        
        # Prepare page properties
        page_properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        }
        
        # Add custom properties
        if properties:
            page_properties.update(properties)
        
        try:
            # Create page
            page = await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=page_properties,
                children=blocks[:100]  # Notion limit: 100 blocks per request
            )
            
            # Add remaining blocks if any
            if len(blocks) > 100:
                await self._append_blocks(page["id"], blocks[100:])
            
            logger.info(
                "Page created",
                page_id=page["id"],
                title=title,
                blocks_count=len(blocks)
            )
            
            return page
            
        except APIResponseError as e:
            logger.error(
                "Failed to create page",
                error=str(e),
                title=title
            )
            raise
    
    async def _append_blocks(
        self,
        page_id: str,
        blocks: List[Dict[str, Any]]
    ):
        """Append blocks to a page in batches"""
        batch_size = 100
        
        for i in range(0, len(blocks), batch_size):
            batch = blocks[i:i + batch_size]
            await self._rate_limit()
            
            await self.client.blocks.children.append(
                block_id=page_id,
                children=batch
            )
    
    async def update_page(
        self,
        page_id: str,
        blocks: List[Dict[str, Any]],
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing page
        
        Args:
            page_id: Page ID to update
            blocks: New content blocks
            properties: Updated properties
            
        Returns:
            Updated page object
        """
        await self._rate_limit()
        
        try:
            # Update properties if provided
            if properties:
                page = await self.client.pages.update(
                    page_id=page_id,
                    properties=properties
                )
            else:
                page = await self.client.pages.retrieve(page_id=page_id)
            
            # Delete existing blocks
            existing_blocks = await self._get_page_blocks(page_id)
            for block in existing_blocks:
                await self._rate_limit()
                await self.client.blocks.delete(block_id=block["id"])
            
            # Add new blocks
            await self._append_blocks(page_id, blocks)
            
            logger.info(
                "Page updated",
                page_id=page_id,
                blocks_count=len(blocks)
            )
            
            return page
            
        except APIResponseError as e:
            logger.error(
                "Failed to update page",
                error=str(e),
                page_id=page_id
            )
            raise
    
    async def _get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """Get all blocks from a page"""
        await self._rate_limit()
        
        blocks = []
        start_cursor = None
        
        while True:
            response = await self.client.blocks.children.list(
                block_id=page_id,
                start_cursor=start_cursor
            )
            
            blocks.extend(response["results"])
            
            if not response["has_more"]:
                break
            
            start_cursor = response["next_cursor"]
            await self._rate_limit()
        
        return blocks
    
    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get page details"""
        await self._rate_limit()
        
        try:
            page = await self.client.pages.retrieve(page_id=page_id)
            return page
        except APIResponseError as e:
            logger.error("Failed to get page", error=str(e), page_id=page_id)
            raise
    
    async def search_pages(
        self,
        query: str,
        filter_properties: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for pages in the database"""
        await self._rate_limit()
        
        try:
            response = await self.client.search(
                query=query,
                filter={
                    "property": "object",
                    "value": "page"
                }
            )
            
            return response["results"]
            
        except APIResponseError as e:
            logger.error("Failed to search pages", error=str(e), query=query)
            raise
    
    async def delete_page(self, page_id: str):
        """Archive (delete) a page"""
        await self._rate_limit()
        
        try:
            await self.client.pages.update(
                page_id=page_id,
                archived=True
            )
            
            logger.info("Page archived", page_id=page_id)
            
        except APIResponseError as e:
            logger.error("Failed to delete page", error=str(e), page_id=page_id)
            raise
    
    def format_documentation(
        self,
        title: str,
        summary: str,
        changes: List[Dict[str, Any]],
        code_examples: List[Dict[str, str]],
        related_files: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Format documentation content as Notion blocks
        
        Args:
            title: Documentation title
            summary: Summary text
            changes: List of changes
            code_examples: List of code examples with language
            related_files: List of related file paths
            
        Returns:
            List of Notion blocks
        """
        blocks = []
        
        # Summary section
        blocks.append(self._create_heading_block("Summary", 2))
        blocks.append(self._create_paragraph_block(summary))
        blocks.append(self._create_divider_block())
        
        # Changes section
        if changes:
            blocks.append(self._create_heading_block("Changes", 2))
            for change in changes:
                change_text = f"{change.get('type', 'Change')}: {change.get('description', '')}"
                blocks.append(self._create_bulleted_list_block(change_text))
            blocks.append(self._create_divider_block())
        
        # Code examples section
        if code_examples:
            blocks.append(self._create_heading_block("Code Examples", 2))
            for example in code_examples:
                blocks.append(
                    self._create_code_block(
                        example.get("code", ""),
                        example.get("language", "python")
                    )
                )
            blocks.append(self._create_divider_block())
        
        # Related files section
        if related_files:
            blocks.append(self._create_heading_block("Related Files", 2))
            for file_path in related_files:
                blocks.append(self._create_bulleted_list_block(file_path))
        
        return blocks


# Global instance
notion_service = NotionService()

# Made with Bob
