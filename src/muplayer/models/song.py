from pydantic import BaseModel, ConfigDict, Field, field_validator


class Song(BaseModel):
    # Permite que o Pydantic leia diretamente objetos de ORM usando `model_validate`
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    title: str
    artist: str
    album: str = "YouTube Audio"
    duration: int = Field(default=0, ge=0)
    source: str | None = None

    @field_validator("duration", mode="before")
    @classmethod
    def validate_duration(cls, v: int | float | None) -> int:
        """Clamps duration to 0 if None or negative (DT-17)."""
        if v is None or v < 0:
            return 0
        return int(v)
