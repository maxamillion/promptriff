"""Database models and operations using aiosqlite."""

import json
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class Conversation:
    """Conversation model."""
    
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    title: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "Conversation":
        """Create from database row."""
        data = dict(row)
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class Prompt:
    """Prompt model."""
    
    id: Optional[int] = None
    conversation_id: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    content: str = ""
    active_tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['active_tools'] = json.dumps(self.active_tools)
        data['metadata'] = json.dumps(self.metadata)
        return data
    
    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "Prompt":
        """Create from database row."""
        data = dict(row)
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['active_tools'] = json.loads(data['active_tools'])
        data['metadata'] = json.loads(data['metadata'])
        return cls(**data)


@dataclass
class Response:
    """Response model."""
    
    id: Optional[int] = None
    prompt_id: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    content: str = ""
    model_provider: str = ""
    model_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['metadata'] = json.dumps(self.metadata)
        return data
    
    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "Response":
        """Create from database row."""
        data = dict(row)
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['metadata'] = json.loads(data['metadata'])
        return cls(**data)


@dataclass
class PromptTemplate:
    """Prompt template model."""
    
    id: Optional[int] = None
    name: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['tags'] = json.dumps(self.tags)
        return data
    
    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "PromptTemplate":
        """Create from database row."""
        data = dict(row)
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['tags'] = json.loads(data['tags'])
        return cls(**data)


class Database:
    """Database manager for PromptRiff."""
    
    def __init__(self, db_path: str):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    async def connect(self) -> aiosqlite.Connection:
        """Create and return a database connection."""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        # Enable foreign keys
        await conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    async def initialize(self):
        """Initialize database schema."""
        async with await self.connect() as conn:
            # Create conversations table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    title TEXT,
                    model_provider TEXT,
                    model_name TEXT
                )
            ''')
            
            # Create prompts table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    content TEXT NOT NULL,
                    active_tools TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                        ON DELETE CASCADE
                )
            ''')
            
            # Create responses table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model_provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
                        ON DELETE CASCADE
                )
            ''')
            
            # Create prompt templates table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Create indexes
            await conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_prompts_conversation '
                'ON prompts(conversation_id)'
            )
            await conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_responses_prompt '
                'ON responses(prompt_id)'
            )
            await conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_conversations_updated '
                'ON conversations(updated_at DESC)'
            )
            
            await conn.commit()
    
    async def create_conversation(
        self,
        title: Optional[str] = None,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            title=title,
            model_provider=model_provider,
            model_name=model_name
        )
        
        async with await self.connect() as conn:
            cursor = await conn.execute(
                '''INSERT INTO conversations 
                   (created_at, updated_at, title, model_provider, model_name)
                   VALUES (?, ?, ?, ?, ?)''',
                (
                    conversation.created_at.isoformat(),
                    conversation.updated_at.isoformat(),
                    conversation.title,
                    conversation.model_provider,
                    conversation.model_name
                )
            )
            conversation.id = cursor.lastrowid
            await conn.commit()
            
        return conversation
    
    async def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """Get a conversation by ID."""
        async with await self.connect() as conn:
            cursor = await conn.execute(
                'SELECT * FROM conversations WHERE id = ?',
                (conversation_id,)
            )
            row = await cursor.fetchone()
            
        return Conversation.from_row(row) if row else None
    
    async def list_conversations(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """List conversations, ordered by most recent."""
        async with await self.connect() as conn:
            cursor = await conn.execute(
                '''SELECT * FROM conversations 
                   ORDER BY updated_at DESC 
                   LIMIT ? OFFSET ?''',
                (limit, offset)
            )
            rows = await cursor.fetchall()
            
        return [Conversation.from_row(row) for row in rows]
    
    async def create_prompt(
        self,
        conversation_id: int,
        content: str,
        active_tools: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Prompt:
        """Create a new prompt."""
        prompt = Prompt(
            conversation_id=conversation_id,
            content=content,
            active_tools=active_tools or [],
            metadata=metadata or {}
        )
        
        async with await self.connect() as conn:
            cursor = await conn.execute(
                '''INSERT INTO prompts 
                   (conversation_id, created_at, content, active_tools, metadata)
                   VALUES (?, ?, ?, ?, ?)''',
                (
                    prompt.conversation_id,
                    prompt.created_at.isoformat(),
                    prompt.content,
                    json.dumps(prompt.active_tools),
                    json.dumps(prompt.metadata)
                )
            )
            prompt.id = cursor.lastrowid
            
            # Update conversation's updated_at
            await conn.execute(
                'UPDATE conversations SET updated_at = ? WHERE id = ?',
                (datetime.now().isoformat(), conversation_id)
            )
            
            await conn.commit()
            
        return prompt
    
    async def create_response(
        self,
        prompt_id: int,
        content: str,
        model_provider: str,
        model_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Response:
        """Create a new response."""
        response = Response(
            prompt_id=prompt_id,
            content=content,
            model_provider=model_provider,
            model_name=model_name,
            metadata=metadata or {}
        )
        
        async with await self.connect() as conn:
            cursor = await conn.execute(
                '''INSERT INTO responses 
                   (prompt_id, created_at, content, model_provider, model_name, metadata)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    response.prompt_id,
                    response.created_at.isoformat(),
                    response.content,
                    response.model_provider,
                    response.model_name,
                    json.dumps(response.metadata)
                )
            )
            response.id = cursor.lastrowid
            await conn.commit()
            
        return response
    
    async def get_conversation_messages(
        self,
        conversation_id: int
    ) -> List[tuple[Prompt, Optional[Response]]]:
        """Get all prompts and responses for a conversation."""
        async with await self.connect() as conn:
            cursor = await conn.execute(
                '''SELECT p.*, r.*
                   FROM prompts p
                   LEFT JOIN responses r ON p.id = r.prompt_id
                   WHERE p.conversation_id = ?
                   ORDER BY p.created_at''',
                (conversation_id,)
            )
            rows = await cursor.fetchall()
            
        messages = []
        for row in rows:
            # Parse prompt columns
            prompt_data = {
                'id': row['id'],
                'conversation_id': row['conversation_id'],
                'created_at': row['created_at'],
                'content': row['content'],
                'active_tools': row['active_tools'],
                'metadata': row['metadata']
            }
            prompt = Prompt.from_row(type('Row', (), prompt_data))
            
            # Parse response columns if present
            response = None
            if row['prompt_id'] is not None:
                response_data = {
                    'id': row['id'],
                    'prompt_id': row['prompt_id'],
                    'created_at': row['created_at'],
                    'content': row['content'],
                    'model_provider': row['model_provider'],
                    'model_name': row['model_name'],
                    'metadata': row['metadata']
                }
                response = Response.from_row(type('Row', (), response_data))
                
            messages.append((prompt, response))
            
        return messages
    
    async def create_or_update_template(
        self,
        name: str,
        content: str,
        tags: Optional[List[str]] = None
    ) -> PromptTemplate:
        """Create or update a prompt template."""
        template = PromptTemplate(
            name=name,
            content=content,
            tags=tags or []
        )
        
        async with await self.connect() as conn:
            # Check if template exists
            cursor = await conn.execute(
                'SELECT id FROM prompt_templates WHERE name = ?',
                (name,)
            )
            existing = await cursor.fetchone()
            
            if existing:
                # Update existing template
                template.id = existing['id']
                template.updated_at = datetime.now()
                await conn.execute(
                    '''UPDATE prompt_templates 
                       SET content = ?, tags = ?, updated_at = ?
                       WHERE id = ?''',
                    (
                        template.content,
                        json.dumps(template.tags),
                        template.updated_at.isoformat(),
                        template.id
                    )
                )
            else:
                # Create new template
                cursor = await conn.execute(
                    '''INSERT INTO prompt_templates 
                       (name, content, tags, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?)''',
                    (
                        template.name,
                        template.content,
                        json.dumps(template.tags),
                        template.created_at.isoformat(),
                        template.updated_at.isoformat()
                    )
                )
                template.id = cursor.lastrowid
                
            await conn.commit()
            
        return template
    
    async def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        async with await self.connect() as conn:
            cursor = await conn.execute(
                'SELECT * FROM prompt_templates WHERE name = ?',
                (name,)
            )
            row = await cursor.fetchone()
            
        return PromptTemplate.from_row(row) if row else None
    
    async def list_templates(self) -> List[PromptTemplate]:
        """List all templates."""
        async with await self.connect() as conn:
            cursor = await conn.execute(
                'SELECT * FROM prompt_templates ORDER BY name'
            )
            rows = await cursor.fetchall()
            
        return [PromptTemplate.from_row(row) for row in rows]
    
    async def backup(self, backup_path: Optional[Path] = None):
        """Create a backup of the database."""
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.db_path.with_suffix(f'.backup.{timestamp}')
            
        async with await self.connect() as conn:
            async with aiosqlite.connect(backup_path) as backup_conn:
                await conn.backup(backup_conn)
                
        return backup_path