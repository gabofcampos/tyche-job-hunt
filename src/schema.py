from dataclasses import dataclass

@dataclass
class Job:
    company: str
    role: str
    location: str
    tags: str
