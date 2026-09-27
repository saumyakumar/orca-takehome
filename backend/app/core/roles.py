from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    COUNTRY_LEAD = "country_lead"
    FIELD_WORKER = "field_worker"
    AUDITOR = "auditor"
