"""Traduction de l'etat des mois en schemas d'API."""

from src.modules.months.domain.entities.month import Month
from src.modules.months.presentation.api.schemas.month_schemas import MonthResponse


def to_month_response(month: Month) -> MonthResponse:
    return MonthResponse(
        user_id=month.user_id,
        mois=month.mois,
        state=month.state,
        is_writable=month.is_writable,
        validated_at=month.validated_at,
        validated_by=month.validated_by,
        reopened_at=month.reopened_at,
        reopened_by=month.reopened_by,
    )
