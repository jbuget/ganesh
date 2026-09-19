# ---------------------------------------------------------------------------
# Production image for the Ganesh API.
#
# Built for linux/arm64 by CI and pushed to GHCR: the host is a Graviton
# instance, which never builds anything itself.
#
# Alembic and its migrations travel with the image — the application does not
# migrate at start-up, the deploy runs `alembic upgrade head` inside the
# running container, once, rather than in every worker that boots.
# ---------------------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first: the layer only rebuilds when requirements.txt moves.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini .
# `make catalog` is run on the host to feed waat.tools.
COPY scripts ./scripts

# Nothing here needs root, and a container that cannot write its own code is
# one less thing to worry about.
RUN useradd --create-home --uid 10001 ganesh \
    && chown -R ganesh:ganesh /app
USER ganesh

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
