"""How the platform is read back, and what never crosses."""

from src.modules.admin.domain.entities.platform import Door, read_door, read_wiring

WIRED = {
    "environment": "production",
    "require_auth": True,
    "auth_entra": True,
    "tenant_id": "tenant-1",
    "gemini_api_key": "a-secret",
    "gemini_model": "gemini-3.8-flash",
    "smtp_host": "smtp.mailgun.org",
    "smtp_port": 587,
    "s3_bucket": "ganesh-attachments",
    "s3_endpoint_url": "",
}


def by_name(wiring, name: str):
    return next(service for service in wiring.services if service.name == name)


def test_entra_is_the_door_when_authentication_is_required() -> None:
    assert read_door(require_auth=True, auth_entra=True) is Door.ENTRA


def test_the_fallback_door_is_the_one_entra_switched_off_leaves() -> None:
    assert read_door(require_auth=True, auth_entra=False) is Door.LOCAL


def test_no_authentication_outranks_which_door_would_have_been_open() -> None:
    assert read_door(require_auth=False, auth_entra=True) is Door.OPEN


def test_no_secret_crosses_the_reading() -> None:
    """The reading says a key is set. It never says what it is."""
    wiring = read_wiring(**WIRED)

    assert "a-secret" not in repr(wiring)
    assert by_name(wiring, "gemini").configured is True
    assert by_name(wiring, "gemini").detail == "gemini-3.8-flash"


def test_a_service_nobody_wired_reads_as_such() -> None:
    wiring = read_wiring(**{**WIRED, "gemini_api_key": "", "smtp_host": ""})

    assert by_name(wiring, "gemini").configured is False
    assert by_name(wiring, "smtp").configured is False
    assert by_name(wiring, "smtp").detail == ""


def test_the_mail_server_is_named_by_its_host_and_port() -> None:
    assert by_name(read_wiring(**WIRED), "smtp").detail == "smtp.mailgun.org:587"


def test_the_storage_names_its_endpoint_when_there_is_one() -> None:
    """Empty means the real S3; a laptop points at its MinIO."""
    laptop = read_wiring(**{**WIRED, "s3_endpoint_url": "http://localhost:9000"})

    assert by_name(laptop, "s3").detail == "http://localhost:9000"
    assert by_name(read_wiring(**WIRED), "s3").detail == "ganesh-attachments"


def test_entra_is_not_named_behind_a_door_it_does_not_hold() -> None:
    local = read_wiring(**{**WIRED, "auth_entra": False})

    assert by_name(local, "entra").configured is False
    assert by_name(local, "entra").detail == ""
