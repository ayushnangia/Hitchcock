from pydantic import BaseModel, ConfigDict

class HitchcockBaseModel(BaseModel):
    """Base model for all Hitchcock models with common configuration."""
    model_config = ConfigDict(
        frozen=True,  # Make models immutable
        validate_assignment=True,  # Validate during assignment
        populate_by_name=True  # Allow population by field name
    )
