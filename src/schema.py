from dataclasses import dataclass
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
