"""What the platform reading is asked for."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformSettings:
    """The environment's answers, unpacked into plain values.

    The settings object itself never crosses into the application: it is a
    pydantic model, and what the layers below know of a framework is nothing.
    A router reads it and hands over what it says.

    No secret is among these fields, and none ever will be — what a service is
    asked is whether it is wired, never with what.
    """

    environment: str
    require_auth: bool
    auth_entra: bool
    tenant_id: str
    has_gemini_key: bool
    gemini_model: str
    smtp_host: str
    smtp_port: int
    s3_bucket: str
    s3_endpoint_url: str
