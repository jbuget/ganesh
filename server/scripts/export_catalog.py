"""Writes the service catalogue to a file.

The catalogue is served by `GET /api/v1/projects/catalog`, which is where
waat.tools will read it once Janus is deployed. Until then this script does
the same work against the database directly, so the file can be committed into
the catalogue's repository and the two sides can already be wired together.

    make catalog                      # writes catalog.json here
    make catalog OUT=../../waat-tools/content/catalog.json

Both routes produce the same JSON: swapping one for the other later changes the
pipe, not the contract.
"""

import asyncio
import json
import sys
from pathlib import Path

from src.core.database import AsyncSessionLocal
from src.modules.projects.application.use_cases.export_catalog import (
    ExportCatalogUseCase,
)
from src.modules.projects.infrastructure.database.repositories.project_assignee_repository_impl import (  # noqa: E501
    SqlProjectAssigneeRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_detail_repository_impl import (  # noqa: E501
    SqlProjectDetailRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (  # noqa: E501
    SqlProjectRepository,
)
from src.modules.projects.presentation.api.mappers.project_mapper import (
    to_catalog_entry_response,
)
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (  # noqa: E501
    SqlUserRepository,
)

DEFAULT_OUT = Path("catalog.json")


async def export(destination: Path) -> int:
    async with AsyncSessionLocal() as session:
        use_case = ExportCatalogUseCase(
            projects=SqlProjectRepository(session),
            details=SqlProjectDetailRepository(session),
            assignees=SqlProjectAssigneeRepository(session),
            users=SqlUserRepository(session),
        )
        entries = await use_case.execute()

    # Through the response schema, so the file and the route cannot drift: one
    # shape, described in one place.
    payload = [
        to_catalog_entry_response(entry).model_dump(mode="json", by_alias=True)
        for entry in entries
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return len(payload)


def main() -> None:
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    count = asyncio.run(export(destination))
    print(f"{count} service(s) written to {destination}")


if __name__ == "__main__":
    main()
