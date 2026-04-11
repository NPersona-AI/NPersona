"""Job model – tracks document processing pipeline state."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    simulation_prompt = Column(Text, nullable=True)
    status = Column(
        String(50),
        nullable=False,
        default="uploaded",
        # stages: uploaded → parsing → graph_building → graph_ready →
        #         persona_generating → scoring → done → error
    )
    error_message = Column(Text, nullable=True)
    document_text = Column(Text, nullable=True)
    graph_data = Column(Text, nullable=True)  # JSON-serialized KnowledgeGraph
    node_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    user_persona_count = Column(Integer, default=0)
    adversarial_persona_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
