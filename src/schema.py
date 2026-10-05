from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from urllib.parse import urlsplit
from uuid import uuid4


class ApplicationStatus(Enum):
    INTERESTED = "Interested"
    ACTIVE = "Active"
    CLOSED = "Closed"


class CompanyInterestRate(Enum):
    VERY_HIGH = "Very high"
    HIGH = "High"
    SOMEWHAT = "Somewhat"


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
    platform: str = ""
    notes: str = ""

@dataclass
class Company:
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str
    industry: str
    location: str
    work_setup: str | None
    interest: CompanyInterestRate
    tags: str
    website_url: str
    careers_url: str
    contacted: bool
    contacted_on: date | None = None
    why_interested: str
    notes: str = ""


def is_valid_posting_url(url: str) -> bool:
    """Accept only HTTP(S) URLs with a host and no whitespace or control characters."""
    try:
        parsed = urlsplit(url)
        # Accessing port also validates non-numeric and out-of-range ports.
        parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.hostname)
        and not any(char.isspace() or ord(char) < 32 for char in url)
        and "\\" not in url
    )
