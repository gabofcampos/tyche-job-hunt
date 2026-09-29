from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from uuid import uuid4


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
    id: str = field(default_factory=lambda: str(uuid4()))
