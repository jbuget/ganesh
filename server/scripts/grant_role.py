"""Hands a role out from the command line, and nowhere else.

The one gesture the application cannot perform on itself: an administrator is
made by an administrator, and the first one has nobody above them. This is
that door — a shell on the host, which is a right of its own.

    python -m scripts.grant_role j.buget@waat.fr ADMIN

It refuses an account it cannot find rather than creating one: somebody who
has never signed in has no Entra id, and an account made here would sit beside
the one their first sign-in creates. Seed them instead — matching by email is
what lets the seed pre-assign a role before anybody has logged in.

Nothing is traced. The register records who did what inside Ganesh, and this
happened outside it: an actor the audit could name would be a fiction.
"""

import asyncio
import logging
import sys

from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.modules.users.domain.entities.user import Role
from src.modules.users.infrastructure.database.models.user_model import UserModel

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("grant_role")


async def grant(email: str, role: Role) -> int:
    async with AsyncSessionLocal() as session:
        model = (
            await session.execute(
                select(UserModel).where(UserModel.email == email.strip().lower())
            )
        ).scalar_one_or_none()
        if model is None:
            logger.error("Aucun compte pour « %s ».", email)
            return 1

        previous = model.role
        model.role = role
        await session.commit()
        logger.info("%s : %s → %s", model.email, previous.value, role.value)
        return 0


def main() -> int:
    if len(sys.argv) != 3:
        logger.error("Usage : python -m scripts.grant_role <email> <ROLE>")
        logger.error("Rôles : %s", ", ".join(role.value for role in Role))
        return 2
    email, raw = sys.argv[1], sys.argv[2].upper()
    try:
        role = Role(raw)
    except ValueError:
        logger.error("Rôle inconnu : %s", raw)
        logger.error("Rôles : %s", ", ".join(role.value for role in Role))
        return 2
    return asyncio.run(grant(email, role))


if __name__ == "__main__":
    raise SystemExit(main())
