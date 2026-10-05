from src.schema import Company


def filter_companies(
    companies: list[Company],
    *,
    query: str = "",
    name: str = "",
    filters: dict[str, str | None] | None = None,
    descending: bool = False,
) -> list[Company]:
    """Return matching companies sorted by name without changing the input list."""
    query = query.strip().casefold()
    name = name.strip().casefold()
    filters = filters or {}
    visible = []
    for company in companies:
        if name not in company.name.casefold():
            continue
        if (
            query
            not in " ".join([company.name, company.tags, company.notes]).casefold()
        ):
            continue
        if any(
            value is not None
            and value
            not in (
                [company.interest.value]
                if field == "interest"
                else (
                    (
                        [company.work_setup.value]
                        if company.work_setup is not None
                        else []
                    )
                    if field == "work_setup"
                    else [
                        part.strip()
                        for part in (getattr(company, field) or "").split(",")
                    ]
                )
            )
            for field, value in filters.items()
        ):
            continue
        visible.append(company)
    visible.sort(key=lambda company: company.name.casefold(), reverse=descending)
    return visible
