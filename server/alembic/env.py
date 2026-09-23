"""Alembic environment, wired to the application's async engine."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.core.config import get_settings
from src.core.database import Base

# Import every model here so Alembic sees them on autogenerate.
from src.modules.audit_logs.infrastructure.database.models import (  # noqa: F401, E402
    audit_log_model,
)
from src.modules.calendar.infrastructure.database.models import (  # noqa: F401, E402
    holiday_model,
)
from src.modules.api_keys.infrastructure.database.models import (  # noqa: F401, E402
    api_key_models,
)
from src.modules.entries.infrastructure.database.models import (  # noqa: F401, E402
    entry_model,
)
from src.modules.gazette.infrastructure.database.models import (  # noqa: F401, E402
    gazette_digest_model,
)
from src.modules.months.infrastructure.database.models import (  # noqa: F401, E402
    month_model,
)
from src.modules.moods.infrastructure.database.models import (  # noqa: F401, E402
    mood_model,
)
from src.modules.notifications.infrastructure.database.models import (  # noqa: F401, E402
    notification_model,
)
from src.modules.planning.infrastructure.database.models import (  # noqa: F401, E402
    simulation_model,
)
from src.modules.projects.infrastructure.database.models import (  # noqa: F401, E402
    project_assignee_model,
    project_attachment_model,
    project_detail_models,
    project_update_model,
    project_model,
    update_reaction_model,
)
from src.modules.users.infrastructure.database.models import (  # noqa: F401, E402
    user_model,
)

# The clock's own ledger: not a business module, but a table all the same, and
# one autogenerate would not see without this.
from src.scheduler import claim  # noqa: F401, E402

config = context.config
if not config.get_main_option("sqlalchemy.url", None):
    config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generates the SQL without connecting to the database."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Applies the migrations through the async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
