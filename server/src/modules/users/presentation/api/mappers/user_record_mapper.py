"""Translating a teammate's record into API schemas."""

from src.modules.users.application.dtos.user_record_dto import UserRecord
from src.modules.users.presentation.api.schemas.rhythm_schemas import to_rhythm_response
from src.modules.users.presentation.api.schemas.user_record_schemas import (
    DeclaredMissionResponse,
    DeclaredWindowResponse,
    MonthFillingResponse,
    RecordedMissionResponse,
    UserRecordResponse,
)


def to_user_record_response(record: UserRecord) -> UserRecordResponse:
    return UserRecordResponse(
        user_id=record.user_id,
        missions=[
            RecordedMissionResponse(
                project_id=mission.project_id,
                label=mission.label,
                status=mission.status,
                is_lead=mission.is_lead,
            )
            for mission in record.missions
        ],
        declared=DeclaredWindowResponse(
            since=record.declared.since,
            until=record.declared.until,
            days=record.declared.days,
            missions=[
                DeclaredMissionResponse(
                    project_id=mission.project_id,
                    label=mission.label,
                    days=mission.days,
                    is_off_project=mission.is_off_project,
                )
                for mission in record.declared.missions
            ],
        ),
        months=[
            MonthFillingResponse(
                month=filling.month,
                delivered=filling.delivered,
                forecast=filling.forecast,
                working_days=filling.working_days,
                elapsed_working_days=filling.elapsed_working_days,
                state=filling.state,
                validated_at=filling.validated_at,
            )
            for filling in record.months
        ],
        rhythms=[
            to_rhythm_response(
                rhythm,
                is_in_force=rhythm.effective_from
                == (record.rhythm.effective_from if record.rhythm else None),
            )
            for rhythm in record.rhythms
        ],
    )
