"""What the administration screen reads."""

from pydantic import BaseModel

from src.modules.admin.domain.entities.platform import Door


class ServiceResponse(BaseModel):
    """One service Ganesh leans on, and whether it is wired."""

    name: str
    configured: bool
    detail: str


class PlatformResponse(BaseModel):
    """The platform as an administrator reads it. No secret crosses."""

    environment: str
    door: Door
    services: list[ServiceResponse]
