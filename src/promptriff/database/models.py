"""Database models for PromptRiff."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    pass


class Conversation(Base):
    """Conversation model representing a chat session."""
    
    __tablename__ = "conversations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model_provider: Mapped[str] = mapped_column(String(50))
    model_name: Mapped[str] = mapped_column(String(100))
    
    # Relationships
    prompts: Mapped[List["Prompt"]] = relationship(
        "Prompt", back_populates="conversation", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Conversation(id={self.id}, title='{self.title}')>"


class Prompt(Base):
    """Prompt model representing a user input."""
    
    __tablename__ = "prompts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    content: Mapped[str] = mapped_column(Text)
    active_tools: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="prompts"
    )
    responses: Mapped[List["Response"]] = relationship(
        "Response", back_populates="prompt", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Prompt(id={self.id}, conversation_id={self.conversation_id})>"


class Response(Base):
    """Response model representing an AI model response."""
    
    __tablename__ = "responses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("prompts.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    content: Mapped[str] = mapped_column(Text)
    model_provider: Mapped[str] = mapped_column(String(50))
    model_name: Mapped[str] = mapped_column(String(100))
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="responses")
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Response(id={self.id}, prompt_id={self.prompt_id})>"


class PromptTemplate(Base):
    """Prompt template model for reusable prompts."""
    
    __tablename__ = "prompt_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<PromptTemplate(id={self.id}, name='{self.name}')>"


class DatabaseManager:
    """Database manager for handling connections and sessions."""
    
    def __init__(self, database_url: str):
        """Initialize database manager.
        
        Args:
            database_url: SQLite database URL
        """
        # Convert to async URL if needed
        if database_url.startswith("sqlite:///"):
            self.async_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        else:
            self.async_url = database_url
            
        self.engine = create_async_engine(
            self.async_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in self.async_url else {}
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        async with self.async_session() as session:
            yield session
    
    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()