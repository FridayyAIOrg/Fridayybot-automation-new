import config
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine, ForeignKey
from sqlalchemy.future import select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import asyncio
import logging

# Suppress SQLAlchemy engine logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    name = Column(String(100), nullable=True, default=None)  # new field for tool name
    tool_call_id = Column(String(100), nullable=True, default=None)  # new field for tool call id
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# DB setup
DATABASE_URL = config.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# DB operations
async def save_message_orm(conversation_id, role, content, name=None, tool_call_id=None):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                name=name,
                tool_call_id=tool_call_id
            )
            session.add(message)

async def get_conversation_messages_orm(conversation_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.id)
        )
        return result.scalars().all()
