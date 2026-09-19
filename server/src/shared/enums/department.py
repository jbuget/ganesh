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
