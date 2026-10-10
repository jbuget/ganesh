"""The routes the administration reads the assistant through, and their one door."""

import csv
import io
import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.assistant.application.use_cases.annotate_exchange import (
    AnnotateExchangeUseCase,
)
from src.modules.assistant.application.use_cases.export_exchanges import (
    ExportExchangesUseCase,
)
from src.modules.assistant.application.use_cases.list_conversations import (
    ListConversationsUseCase,
)
from src.modules.assistant.application.use_cases.read_conversation import (
    ReadConversationUseCase,
)
from src.modules.assistant.application.use_cases.read_indicators import (
    ReadIndicatorsUseCase,
)
from src.modules.assistant.domain.entities.exchange import Exchange, Verdict
from src.modules.assistant.presentation.dependencies import (
    get_annotate_exchange_use_case,
    get_export_exchanges_use_case,
    get_list_conversations_use_case,
    get_read_conversation_use_case,
    get_read_indicators_use_case,
)
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.assistant import ANSWER
from tests.helpers.in_memory_repositories import (
    InMemoryExchangeArchive,
    InMemoryExchangeRepository,
    InMemoryUserRepository,
)

STUDY = f"{get_settings().api_prefix}/admin/assistant"
ADMIN = User(9, "oid-9", "a.admin@waat.fr", "A. Admin", role=Role.ADMIN)
LEA = User(1, "oid-1", "l.chen@waat.fr", "L. Chen", role=Role.TEAMMATE)
ASKED_AT = datetime(2026, 10, 8, 9, 30, tzinfo=UTC)


@dataclass
class Study:
    client: AsyncClient
    store: InMemoryExchangeRepository


def open_study(person: User = ADMIN) -> Study:
    store = InMemoryExchangeRepository()
    archive = InMemoryExchangeArchive(store)
    app.dependency_overrides[get_current_user] = lambda: person
    app.dependency_overrides[get_list_conversations_use_case] = (
        lambda: ListConversationsUseCase(archive)
    )
    app.dependency_overrides[get_read_conversation_use_case] = (
        lambda: ReadConversationUseCase(archive)
    )
    app.dependency_overrides[get_read_indicators_use_case] = (
        lambda: ReadIndicatorsUseCase(archive)
    )
    app.dependency_overrides[get_export_exchanges_use_case] = (
        lambda: ExportExchangesUseCase(archive, InMemoryUserRepository([LEA, ADMIN]))
    )
    app.dependency_overrides[get_annotate_exchange_use_case] = (
        lambda: AnnotateExchangeUseCase(archive)
    )
    return Study(
        client=AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        store=store,
    )


async def lea_asked(study: Study, verdict: Verdict | None = None) -> Exchange:
    return await study.store.add(
        Exchange(
            conversation_id=uuid4(),
            rank=1,
            asker_id=LEA.id or 0,
            question="Où en est WAATcher ?",
            answer=ANSWER,
            project_id=7,
            asked_at=ASKED_AT,
            verdict=verdict,
        )
    )


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_an_admin_lists_everybody_s_conversations() -> None:
    study = open_study()
    asked = await lea_asked(study, verdict=Verdict.UNHELPFUL)

    response = await study.client.get(f"{STUDY}/conversations")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    [summary] = body["conversations"]
    assert summary["id"] == str(asked.conversation_id)
    assert summary["asker_id"] == LEA.id
    assert summary["first_question"] == "Où en est WAATcher ?"
    assert (summary["exchange_count"], summary["unhelpful"]) == (1, 1)


async def test_a_period_is_given_in_days_on_the_paris_clock() -> None:
    study = open_study()
    await lea_asked(study)

    before = await study.client.get(
        f"{STUDY}/conversations", params={"to_day": "2026-10-07"}
    )
    on_the_day = await study.client.get(
        f"{STUDY}/conversations",
        params={"from_day": "2026-10-08", "to_day": "2026-10-08"},
    )

    assert before.json()["total"] == 0
    assert on_the_day.json()["total"] == 1


async def test_a_conversation_reads_with_what_every_tool_read_back() -> None:
    study = open_study()
    asked = await lea_asked(study)

    response = await study.client.get(f"{STUDY}/conversations/{asked.conversation_id}")

    assert response.status_code == 200
    [exchange] = response.json()["exchanges"]
    assert exchange["consultations"] == [
        {"tool": "project_brief", "arguments": {"project_id": 7}, "result": "WAATcher…"}
    ]
    assert (exchange["model"], exchange["elapsed_ms"]) == ("gemini-test", 1200)


async def test_a_conversation_nobody_had_is_not_found() -> None:
    response = await open_study().client.get(f"{STUDY}/conversations/{uuid4()}")

    assert response.status_code == 404


async def test_the_indicators_name_every_cause_and_how_far_back_they_go() -> None:
    study = open_study()
    await lea_asked(study, verdict=Verdict.HELPFUL)

    response = await study.client.get(f"{STUDY}/indicators")

    body = response.json()
    assert (body["questions"], body["helpful"]) == (1, 1)
    assert [held["cause"] for held in body["causes"]] == [
        "wrong_reading",
        "wrong_phrasing",
        "out_of_scope",
        "right_answer",
    ]
    assert body["tools"] == [{"tool": "project_brief", "count": 1}]
    assert body["kept_since"] == "2026-10-08T09:30:00Z"


async def test_an_admin_annotates_an_answer() -> None:
    study = open_study()
    asked = await lea_asked(study)

    response = await study.client.put(
        f"{STUDY}/exchanges/{asked.id}/annotation",
        json={"cause": "wrong_reading", "note": "Les lots manquent."},
    )

    assert response.status_code == 200
    annotation = response.json()["annotation"]
    assert annotation["cause"] == "wrong_reading"
    assert annotation["annotated_by"] == ADMIN.id


async def test_the_csv_export_opens_in_a_spreadsheet_and_names_whoever_asked() -> None:
    study = open_study()
    await lea_asked(study)

    response = await study.client.get(f"{STUDY}/exchanges/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith("﻿".encode())
    rows = list(csv.DictReader(io.StringIO(response.text.lstrip("﻿")), delimiter=";"))
    assert [(row["asker_name"], row["tools"]) for row in rows] == [
        ("L. Chen", "project_brief")
    ]


async def test_the_json_export_carries_the_tools_readings_whole() -> None:
    study = open_study()
    await lea_asked(study)

    response = await study.client.get(
        f"{STUDY}/exchanges/export", params={"format": "json"}
    )

    [exported] = json.loads(response.content)
    assert exported["asker_email"] == "l.chen@waat.fr"
    assert exported["consultations"][0]["result"] == "WAATcher…"


@pytest.mark.parametrize("role", [Role.GUEST, Role.TEAMMATE, Role.MANAGER])
@pytest.mark.parametrize(
    "method, path",
    [
        ("GET", "/conversations"),
        ("GET", f"/conversations/{uuid4()}"),
        ("GET", "/indicators"),
        ("GET", "/exchanges/export"),
        ("PUT", "/exchanges/1/annotation"),
    ],
)
async def test_nobody_below_an_admin_reads_anybody_s_exchanges(
    role: Role, method: str, path: str
) -> None:
    """Somebody else's questions are read for study, and only by an admin."""
    study = open_study(User(2, "oid-2", "m@waat.fr", "M. M", role=role))

    response = await study.client.request(
        method, f"{STUDY}{path}", json={"cause": "right_answer"}
    )

    assert response.status_code == 403
