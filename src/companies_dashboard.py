import streamlit as st

from src.schema import Company, is_valid_posting_url

COLUMN_WIDTHS = [2, 1.4, 1.4, 1.3, 1.3, 1.6, 0.6]
PAGE_SIZE = 6


def clear_company_filters() -> None:
    for key in (
        "search",
        "name",
        "industry",
        "location",
        "work_setup",
        "interest",
        "tags",
    ):
        st.session_state.pop(f"companies_{key}", None)
    st.session_state.companies_page = 1


def render_company_details(company: Company | None) -> None:
    with st.container(border=True, height=650):
        title, close = st.columns([5, 1])
        title.subheader("Company details")
        if close.button(
            "Close",
            icon=":material/close:",
            key="close_company_details",
            disabled=company is None,
        ):
            st.session_state.selected_company_id = None
            st.rerun()
        if company is None:
            st.info("Select a company to see its details.")
            return
        st.subheader(company.name)
        st.badge(f"{company.interest.value} interest", color="green")
        st.caption(
            " · ".join(
                filter(None, [company.industry, company.location, company.work_setup])
            )
        )
        st.divider()
        st.caption("WHY I SAVED IT")
        st.text(company.why_interested or "No reason added yet.")
        st.caption("TAGS")
        with st.container(horizontal=True):
            for tag in company.tags.split(","):
                if tag.strip():
                    st.badge(tag.strip(), color="gray")
        st.caption("LINKS")
        with st.container(horizontal=True):
            for label, url in (
                ("Website", company.website_url),
                ("Careers", company.careers_url),
            ):
                if is_valid_posting_url(url):
                    st.link_button(label, url, icon=":material/open_in_new:")
        st.divider()
        st.caption("LINKED JOBS")
        st.caption("Job linking is not available yet.")
        st.button(
            "Edit company",
            icon=":material/edit:",
            type="primary",
            key="edit_company",
            disabled=True,
            width="stretch",
        )


def render_companies_dashboard(companies: list[Company] | None = None) -> None:
    companies = companies or []
    heading, add = st.columns([4, 1], vertical_alignment="center")
    with heading:
        st.header("Companies")
        st.caption("Places I would like to work, independent of any application.")
    add.button(
        "Add company",
        icon=":material/add:",
        type="primary",
        key="add_company",
        disabled=True,
        width="stretch",
        help="Company creation is coming soon.",
    )

    table, details = st.columns([5, 2], gap="medium")
    with table, st.container(border=True, height=650):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.subheader("All companies")
            st.caption(str(len(companies)))
        search_col, sort_col, clear_col = st.columns(
            [4, 1.4, 1.2], vertical_alignment="bottom"
        )
        query = (
            search_col.text_input(
                "Search companies",
                placeholder="Company name, tags or notes...",
                key="companies_search",
                label_visibility="collapsed",
            )
            .strip()
            .casefold()
        )
        sort = sort_col.selectbox(
            "Sort companies",
            ["Name A–Z", "Name Z–A"],
            key="companies_sort",
            label_visibility="collapsed",
        )
        clear_col.button(
            "Clear filters", on_click=clear_company_filters, key="clear_company_filters"
        )
        columns = st.columns(COLUMN_WIDTHS)
        name = (
            columns[0]
            .text_input("Company", placeholder="Search", key="companies_name")
            .strip()
            .casefold()
        )
        filters = {}
        for column, field, label in zip(
            columns[1:6],
            ("industry", "location", "work_setup", "interest", "tags"),
            ("Industry", "Location", "Work setup", "Interest", "Tags"),
        ):
            values = set()
            for company in companies:
                value = (
                    company.interest.value
                    if field == "interest"
                    else getattr(company, field)
                )
                values.update(
                    part.strip() for part in (value or "").split(",") if part.strip()
                )
            filters[field] = column.selectbox(
                label,
                sorted(values),
                index=None,
                placeholder="All",
                key=f"companies_{field}",
            )
        columns[6].markdown("Jobs")
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
                    else [
                        part.strip()
                        for part in (getattr(company, field) or "").split(",")
                    ]
                )
                for field, value in filters.items()
            ):
                continue
            visible.append(company)
        visible.sort(
            key=lambda company: company.name.casefold(), reverse=sort == "Name Z–A"
        )
        pages = max(1, (len(visible) + PAGE_SIZE - 1) // PAGE_SIZE)
        st.session_state.companies_page = min(
            st.session_state.get("companies_page", 1), pages
        )
        page = st.session_state.companies_page
        st.divider()
        for company in visible[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]:
            row = st.columns(COLUMN_WIDTHS, vertical_alignment="center")
            if row[0].button(
                company.name,
                key=f"company_{company.id}",
                width="stretch",
                type=(
                    "primary"
                    if st.session_state.get("selected_company_id") == company.id
                    else "tertiary"
                ),
            ):
                st.session_state.selected_company_id = company.id
                st.rerun()
            row[1].text(company.industry or "—")
            row[2].text(company.location or "—")
            row[3].text(company.work_setup or "—")
            row[4].badge(company.interest.value, color="green")
            row[5].text(company.tags or "—")
            row[6].text("—")
            st.divider()
        if not visible:
            st.info(
                "No companies match your filters."
                if companies
                else "No companies saved yet."
            )
        st.caption(
            f"Showing {min(PAGE_SIZE, max(0, len(visible) - (page - 1) * PAGE_SIZE))} of {len(visible)} companies"
        )
        st.selectbox(
            "Page", range(1, pages + 1), key="companies_page", disabled=pages == 1
        )
    selected = next(
        (
            company
            for company in companies
            if company.id == st.session_state.get("selected_company_id")
        ),
        None,
    )
    with details:
        render_company_details(selected)
    st.caption(
        "Select a company name to inspect it. Each column filter narrows the table."
    )
