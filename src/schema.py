from dataclasses import dataclass
from datetime import date
from enum import Enum


class ApplicationStatus(Enum):
    INTERESTED = "Interested"
    ACTIVE = "Active"
    CLOSED = "Closed"


@dataclass
class Job:
    company: str
    role: str
    location: str
    tags: str
    status: ApplicationStatus
    applied_on: date | None = None
    stage: str | None = None
    outcome: str | None = None
