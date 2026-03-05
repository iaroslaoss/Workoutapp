import re

from pydantic import BaseModel, ConfigDict, field_validator

TEMPO_PATTERN = re.compile(r"^\d+-\d+-\d+-\d+$")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TempoMixin(BaseModel):
    @field_validator("default_tempo", "tempo", check_fields=False)
    @classmethod
    def validate_tempo(cls, value: str | None):
        if value is None:
            return value
        if not TEMPO_PATTERN.match(value):
            raise ValueError("Tempo must follow format eccentric-isometricTop-concentric-isometricBottom (e.g., 3-1-1-0)")
        return value
