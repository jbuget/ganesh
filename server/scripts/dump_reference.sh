#!/usr/bin/env bash
#
# Writes the reference data, and only it, ready to be loaded into staging or
# production.
#
# What goes: who the team is, the missions and everything that describes them.
# What stays: what people have done — entries, month states, the audit log — and
# anything holding a secret. A fresh environment gets a referential, not a
# history that did not happen there.
#
# The order of the tables is the order of their dependencies: a dump replayed
# in one transaction checks every foreign key as it goes, and nothing may
# arrive before what it points at.
set -euo pipefail

DATABASE="${1:?usage: dump_reference.sh <database url> [output]}"
OUT="${2:-reference.sql}"

# pg_dump refuses a server newer than itself. Where the client on the PATH is
# behind — a database in Docker, typically — point this at one that is not:
#   PG_DUMP="docker exec timesheet7-db pg_dump" make dump
read -ra DUMPER <<< "${PG_DUMP:-pg_dump}"

TABLES=(
  users
  holidays
  projects
  project_assignees
  project_updates
  project_departments
  project_phases_reached
  project_links
  project_stack
  project_tags
  project_dependencies
)

ARGS=()
for table in "${TABLES[@]}"; do
  ARGS+=(--table="public.${table}")
done

# --data-only: the target already has its schema, put there by the migrations,
# and its own alembic_version — which must not be overwritten by ours.
"${DUMPER[@]}" "$DATABASE" \
  --data-only \
  --no-owner \
  --no-privileges \
  "${ARGS[@]}" \
  > "$OUT"

echo "Ecrit : $OUT ($(wc -l < "$OUT") lignes)"
echo
echo "Pour le charger, sur une base deja migree (alembic upgrade head) :"
echo "  psql <url> --single-transaction -v ON_ERROR_STOP=1 < $OUT"
echo
echo "En une transaction : ou tout entre, ou rien. Les cles etrangeres sont"
echo "verifiees au fil du chargement, l'ordre des tables ci-dessus les respecte."
