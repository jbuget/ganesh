"""The company departments, named once for the whole application."""

from enum import StrEnum


class Department(StrEnum):
    """Company department.

    A mission serves one or several of them; a teammate belongs to one. The
    list is the same on both sides — one does not steer a portfolio by
    department if the teams do not read under the same names.
    """

    FINANCE_ADMIN = "finance_admin"
    LANDLORDS = "landlords"
    CONDOMINIUM = "condominium"
    CUSTOMER_SERVICE = "customer_service"
    OPERATIONS = "operations"
    INFORMATION_SYSTEMS = "information_systems"
    HUMAN_RESOURCES = "human_resources"
    MARKETING_COMMUNICATION_CSR = "marketing_communication_csr"
    COMMERCIAL_REAL_ESTATE = "commercial_real_estate"
    OTHER = "other"


#: Rank of each department in the order declared above.
_ORDER = {department: rank for rank, department in enumerate(Department)}


def in_declared_order(departments: list[Department]) -> list[Department]:
    """The departments sorted as they are declared, duplicates dropped.

    A mission concerns several of them, and nothing in the database says in
    which order: sorting them here is what keeps a row reading the same way
    from one load to the next, and the same way as the picker offers them.
    """
    return sorted(dict.fromkeys(departments), key=lambda d: _ORDER[d])
