"""Persona model – stores generated user-centric and adversarial personas."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, JSON
from app.database import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), nullable=False, index=True)

    # --- Team ---
    team = Column(String(20), nullable=False)  # "user_centric" or "adversarial"

    # --- Common Fields ---
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # --- User-Centric Fields ---
    role = Column(String(255), nullable=True)
    tech_literacy = Column(String(20), nullable=True)  # low/medium/high
    domain_expertise = Column(String(20), nullable=True)  # novice/intermediate/expert
    emotional_state = Column(String(50), nullable=True)
    accessibility_needs = Column(JSON, nullable=True)  # list of strings
    typical_tasks = Column(JSON, nullable=True)  # list of strings
    edge_case_behavior = Column(Text, nullable=True)
    edge_case_taxonomy_id = Column(String(10), nullable=True)
    frustration_level = Column(Integer, nullable=True)  # 1-10
    failure_recovery_expectation = Column(Text, nullable=True)

    # --- Adversarial Fields ---
    alias = Column(String(255), nullable=True)
    skill_level = Column(String(20), nullable=True)  # script_kiddie/intermediate/expert/nation_state
    attack_taxonomy_ids = Column(JSON, nullable=True)  # list of strings
    owasp_mapping = Column(JSON, nullable=True)  # list of strings
    mitre_atlas_id = Column(String(50), nullable=True)
    target_agent = Column(String(255), nullable=True)
    target_data = Column(String(255), nullable=True)
    motivation = Column(Text, nullable=True)
    attack_strategy = Column(String(50), nullable=True)
    persistence_level = Column(Integer, nullable=True)  # 1-10
    evasion_techniques = Column(JSON, nullable=True)  # list of strings
    success_criteria = Column(Text, nullable=True)
    expected_system_response = Column(Text, nullable=True)
    risk_severity = Column(String(20), nullable=True)  # critical/high/medium/low

    # --- Multi-Turn Scenarios ---
    conversation_trajectory = Column(JSON, nullable=True)  # list of turn objects
    playbook = Column(JSON, nullable=True)  # list of step objects
    example_prompts = Column(JSON, nullable=True)  # list of strings

    # --- Scoring ---
    novelty_score = Column(Float, nullable=True)
    coverage_impact = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    composite_score = Column(Float, nullable=True)

    # --- Graph Reference ---
    source_node_id = Column(String(100), nullable=True)
    source_node_type = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
