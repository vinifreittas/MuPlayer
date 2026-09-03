from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    language: str = Field(default="en")
    efficiency_mode: bool = False
    search_limit: int = Field(default=15, ge=1, le=50)
    volume: int = Field(default=80, ge=0, le=100)

    def toggle_efficiency_mode(self) -> bool:
        """Toggles efficiency mode and returns the new state."""
        self.efficiency_mode = not self.efficiency_mode
        return self.efficiency_mode
