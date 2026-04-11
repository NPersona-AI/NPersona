"""Request schemas."""
from pydantic import BaseModel, Field


class GeneratePersonasRequest(BaseModel):
    num_user_personas: int = Field(default=15, ge=1, le=100)
    num_adversarial_personas: int = Field(default=15, ge=1, le=100)


class GenerateMissingRequest(BaseModel):
    taxonomy_id: str = Field(..., description="The taxonomy ID to generate a persona for (e.g., A01, U03)")
