#!/usr/bin/env bash
set -euo pipefail

STATUS="${1}"   # success | failure

# =========================
# Inputs
# =========================
ENV="${ENV}"
SERVICE="${SERVICE}"
BRANCH="${BRANCH}"
COMMIT="${COMMIT}"
AUTHOR="${AUTHOR}"
MESSAGE="${MESSAGE:-}"
RUN_URL="${RUN_URL}"
WEBHOOK_URL="${WEBHOOK_URL}"

# =========================
# sanitize
# =========================
MESSAGE=$(echo "$MESSAGE" \
  | tr '\n' ' ' \
  | sed 's/"/\\"/g' \
  | sed "s/'/\\'/g" \
  | cut -c1-300)

SERVICE=$(echo "$SERVICE" | sed 's/"/\\"/g')
ENV=$(echo "$ENV" | sed 's/"/\\"/g')
BRANCH=$(echo "$BRANCH" | sed 's/"/\\"/g')
AUTHOR=$(echo "$AUTHOR" | sed 's/"/\\"/g')

if [ "$STATUS" = "success" ]; then
  STATUS_INDICATOR="🚀 "
  COLOR="Good"
else
  STATUS_INDICATOR="❌ "
  COLOR="Attention"
fi

# =========================
# payload
# =========================
cat <<EOF > payload.json
{
  "type": "AdaptiveCard",
  "\$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "version": "1.5",
  "body": [
    {
      "type": "TextBlock",
      "text": "${STATUS_INDICATOR} ${SERVICE} | [${ENV^^}]",
      "size": "Large",
      "weight": "Bolder",
      "color": "${COLOR}"
    },
    {
      "type": "FactSet",
      "facts": [
        { "title": "Environment", "value": "${ENV}" },
        { "title": "Branch", "value": "${BRANCH}" },
        { "title": "Author", "value": "${AUTHOR}" },
        { "title": "Commit", "value": "${COMMIT}" }
      ]
    },
    {
      "type": "TextBlock",
      "text": "${MESSAGE}",
      "wrap": true
    }
  ],
  "actions": [
    {
      "type": "Action.OpenUrl",
      "title": "🔍 View Workflow",
      "url": "${RUN_URL}"
    }
  ]
}
EOF

curl -X POST \
  -H "Content-Type: application/json" \
  -d @payload.json \
  "$WEBHOOK_URL"

rm -f payload.json