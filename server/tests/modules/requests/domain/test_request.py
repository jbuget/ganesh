"""The rules a need carries, from the day it is filed to the day it becomes one."""

from datetime import date, datetime

import pytest

from src.modules.requests.domain.entities.request import Request, RequestState
from src.shared.enums.department import Department
from src.shared.exceptions.domain_exceptions import (
    ConflictError,
    ForbiddenActionError,
    ValidationError,
)

AUTHOR = 7
SPONSOR = 3
MANAGER = 1
NOW = datetime(2026, 9, 22, 10, 0)
LATER = datetime(2026, 9, 25, 9, 0)


def make_request(**overrides) -> Request:
    fields: dict = {
        "id": 1,
        "title": "Relances de paiement à la main",
        "requester_id": AUTHOR,
        "departments": [Department.FINANCE_ADMIN],
        "sponsor_ids": [SPONSOR],
        "created_at": NOW,
    }
    fields.update(overrides)
    return Request(**fields)


def filled(**overrides) -> Request:
    """A request carrying everything submitting it asks for."""
    said: dict = {
        "problem": "Les relances sont tapées une par une.",
        "impact": "Trois personnes de la compta, tous les lundis.",
        "expected_outcome": "Une relance partie toute seule le jour dit.",
    }
    said.update(overrides)
    return make_request(**said)


class TestWhatItTakesToExist:
    def test_a_request_starts_as_a_draft(self) -> None:
        assert make_request().state is RequestState.DRAFT

    def test_a_request_without_a_title_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            make_request(title="   ")

    def test_a_title_is_trimmed(self) -> None:
        assert make_request(title="  Relances  ").title == "Relances"

    def test_a_request_concerns_at_least_one_department(self) -> None:
        """Nobody can steer a need nobody can say whose it is."""
        with pytest.raises(ValidationError):
            make_request(departments=[])

    def test_the_departments_read_in_the_order_they_are_declared(self) -> None:
        request = make_request(
            departments=[Department.OPERATIONS, Department.FINANCE_ADMIN]
        )

        assert request.departments == [
            Department.FINANCE_ADMIN,
            Department.OPERATIONS,
        ]

    def test_a_department_named_twice_is_held_once(self) -> None:
        request = make_request(
            departments=[Department.OPERATIONS, Department.OPERATIONS]
        )

        assert request.departments == [Department.OPERATIONS]

    def test_a_request_is_carried_by_at_least_one_sponsor(self) -> None:
        with pytest.raises(ValidationError):
            make_request(sponsor_ids=[])

    def test_a_sponsor_named_twice_is_held_once(self) -> None:
        assert make_request(sponsor_ids=[3, 3, 5]).sponsor_ids == [3, 5]

    def test_a_blank_field_reads_as_unsaid(self) -> None:
        assert make_request(problem="   ").problem is None


class TestSubmitting:
    def test_the_author_submits_their_request(self) -> None:
        request = filled()

        request.submit(by=AUTHOR, at=LATER)

        assert request.state is RequestState.SUBMITTED
        assert request.submitted_at == LATER

    def test_nobody_else_submits_it_for_them(self) -> None:
        """A need is expressed by whoever has it, or it is not theirs."""
        with pytest.raises(ForbiddenActionError):
            filled().submit(by=MANAGER, at=LATER)

    @pytest.mark.parametrize("missing", ["problem", "impact", "expected_outcome"])
    def test_a_request_saying_nothing_is_not_submitted(self, missing: str) -> None:
        request = filled(**{missing: None})

        with pytest.raises(ValidationError):
            request.submit(by=AUTHOR, at=LATER)

    def test_a_request_already_submitted_is_not_submitted_again(self) -> None:
        request = filled()
        request.submit(by=AUTHOR, at=LATER)

        with pytest.raises(ConflictError):
            request.submit(by=AUTHOR, at=LATER)


class TestWritingTheSheet:
    def test_the_author_fills_their_draft_in(self) -> None:
        request = make_request()

        request.fill_in(
            title="Relances de paiement",
            departments=[Department.FINANCE_ADMIN],
            sponsor_ids=[SPONSOR],
            problem="Tapées une par une.",
            impact="Trois personnes.",
            expected_outcome="Une relance automatique.",
            cost_of_inaction="Une demi-journée par semaine.",
            desired_by=date(2026, 12, 31),
            envisaged_solution=None,
            by=AUTHOR,
        )

        assert request.title == "Relances de paiement"
        assert request.problem == "Tapées une par une."
        assert request.desired_by == date(2026, 12, 31)

    def test_nobody_else_writes_it(self) -> None:
        with pytest.raises(ForbiddenActionError):
            make_request().fill_in(
                title="Autre chose",
                departments=[Department.FINANCE_ADMIN],
                sponsor_ids=[SPONSOR],
                problem=None,
                impact=None,
                expected_outcome=None,
                cost_of_inaction=None,
                desired_by=None,
                envisaged_solution=None,
                by=MANAGER,
            )

    def test_a_submitted_request_is_not_rewritten(self) -> None:
        """The decision bears on a text that has stopped moving."""
        request = filled()
        request.submit(by=AUTHOR, at=LATER)

        with pytest.raises(ConflictError):
            request.fill_in(
                title="Autre chose",
                departments=[Department.FINANCE_ADMIN],
                sponsor_ids=[SPONSOR],
                problem=None,
                impact=None,
                expected_outcome=None,
                cost_of_inaction=None,
                desired_by=None,
                envisaged_solution=None,
                by=AUTHOR,
            )


class TestWithdrawing:
    def test_the_author_takes_their_request_back(self) -> None:
        request = filled()
        request.submit(by=AUTHOR, at=LATER)

        request.withdraw(by=AUTHOR)

        assert request.state is RequestState.DRAFT
        assert request.submitted_at is None

    def test_nobody_else_takes_it_back(self) -> None:
        request = filled()
        request.submit(by=AUTHOR, at=LATER)

        with pytest.raises(ForbiddenActionError):
            request.withdraw(by=MANAGER)

    def test_a_request_already_arbitrated_is_not_taken_back(self) -> None:
        request = filled()
        request.submit(by=AUTHOR, at=LATER)
        request.decide(RequestState.ACCEPTED, note=None, by=MANAGER, at=LATER)

        with pytest.raises(ConflictError):
            request.withdraw(by=AUTHOR)


class TestArbitrating:
    def test_a_request_is_accepted(self) -> None:
        request = filled()
        request.submit(by=AUTHOR, at=NOW)

        request.decide(RequestState.ACCEPTED, note=None, by=MANAGER, at=LATER)

        assert request.state is RequestState.ACCEPTED
        assert request.decided_by_id == MANAGER
        assert request.decided_at == LATER

    @pytest.mark.parametrize("decision", [RequestState.REJECTED, RequestState.DEFERRED])
    def test_a_refusal_says_why(self, decision: RequestState) -> None:
        """A « non » with no reason is filed again, word for word, in March."""
        request = filled()
        request.submit(by=AUTHOR, at=NOW)

        with pytest.raises(ValidationError):
            request.decide(decision, note="  ", by=MANAGER, at=LATER)

    def test_a_draft_is_not_arbitrated(self) -> None:
        with pytest.raises(ConflictError):
            filled().decide(RequestState.ACCEPTED, note=None, by=MANAGER, at=LATER)

    def test_the_author_does_not_arbitrate_their_own_request(self) -> None:
        request = filled(requester_id=MANAGER)
        request.submit(by=MANAGER, at=NOW)

        with pytest.raises(ForbiddenActionError):
            request.decide(RequestState.ACCEPTED, note=None, by=MANAGER, at=LATER)

    def test_a_sponsor_does_not_arbitrate_what_they_carry(self) -> None:
        """Whoever carries a need to the COMEX cannot also be the one to weigh it."""
        request = filled(sponsor_ids=[MANAGER])
        request.submit(by=AUTHOR, at=NOW)

        with pytest.raises(ForbiddenActionError):
            request.decide(RequestState.ACCEPTED, note=None, by=MANAGER, at=LATER)

    def test_an_arbitration_is_played_again_as_long_as_nothing_was_built(self) -> None:
        request = filled()
        request.submit(by=AUTHOR, at=NOW)
        request.decide(
            RequestState.DEFERRED, note="Pas ce trimestre.", by=MANAGER, at=NOW
        )

        request.decide(RequestState.ACCEPTED, note=None, by=MANAGER, at=LATER)

        assert request.state is RequestState.ACCEPTED

    @pytest.mark.parametrize(
        "decision", [RequestState.DRAFT, RequestState.SUBMITTED, RequestState.CONVERTED]
    )
    def test_arbitrating_says_one_of_the_three_things_it_can_say(
        self, decision: RequestState
    ) -> None:
        request = filled()
        request.submit(by=AUTHOR, at=NOW)

        with pytest.raises(ValidationError):
            request.decide(decision, note="Peu importe.", by=MANAGER, at=LATER)


class TestConverting:
    def test_an_accepted_request_becomes_a_mission(self) -> None:
        request = filled()
        request.submit(by=AUTHOR, at=NOW)
        request.decide(RequestState.ACCEPTED, note=None, by=MANAGER, at=NOW)

        request.convert(project_id=42, at=LATER)

        assert request.state is RequestState.CONVERTED
        assert request.converted_project_id == 42
        assert request.converted_at == LATER

    def test_a_request_nobody_accepted_becomes_nothing(self) -> None:
        """Even a day's work goes through the COMEX: that is the whole point."""
        request = filled()
        request.submit(by=AUTHOR, at=NOW)

        with pytest.raises(ConflictError):
            request.convert(project_id=42, at=LATER)

    def test_a_converted_request_is_the_end_of_it(self) -> None:
        request = filled()
        request.submit(by=AUTHOR, at=NOW)
        request.decide(RequestState.ACCEPTED, note=None, by=MANAGER, at=NOW)
        request.convert(project_id=42, at=LATER)

        with pytest.raises(ConflictError):
            request.decide(
                RequestState.REJECTED, note="Trop tard.", by=MANAGER, at=LATER
            )


class TestDeleting:
    def test_a_draft_is_deleted_by_its_author(self) -> None:
        assert make_request().may_be_deleted_by(AUTHOR) is True

    def test_nobody_else_deletes_it(self) -> None:
        assert make_request().may_be_deleted_by(MANAGER) is False

    def test_what_has_been_submitted_is_no_longer_deleted(self) -> None:
        """Once read by somebody else, it is withdrawn rather than erased."""
        request = filled()
        request.submit(by=AUTHOR, at=NOW)

        assert request.may_be_deleted_by(AUTHOR) is False
