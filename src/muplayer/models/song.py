from pydantic import BaseModel, ConfigDict


class Song(BaseModel):
    # Permite que o Pydantic leia diretamente objetos de ORM usando `model_validate`
    model_config = ConfigDict(from_attributes=True)

    title: str
    artist: str
    album: str
    duration: int
    source: str | None = None
