# AGENTS.md

## project overview

`tyche-job-hunt` is a personal job-search management application built with python and streamlit.

the app helps track job opportunities, applications, and companies of interest.

## professional context

The user's professional background, career objectives, technical interests, values, and target companies are documented in a separate local Git repository.

**Context entrypoint:** `../career-context/AGENTS.md`

Before performing career-related tasks, agents should consult `../career-context/AGENTS.md`, which routes to:
- `professional_context.md` (candidate profile, skills, experience, and career goals)
- `target_companies_context.md` (employer selection criteria, sector priorities, and company shortlists)

This includes:
- Evaluating job opportunities and company fit.
- Researching potential employers.
- Recommending career directions or learning priorities.
- Drafting CVs, cover letters, or application materials.
- Prioritizing companies and job opportunities.

### context handling rules

1. treat the career-context files as the primary source for the user's stated career preferences and professional background.
2. distinguish verified experience from aspirations, interests, and skills currently being developed.
3. do not invent achievements, technical experience, qualifications, or application statuses.
4. if context files are unavailable, continue with available information and explicitly identify missing context when relevant.
5. do not automatically modify files in the career-context repository when implementing application features.

## privacy and repository boundaries

The `career-context` repository is intentionally local-only and must remain separate from the public `tyche-job-hunt` repository.

Agents must:
- Never copy career-context files into the public repository.
- Never commit or push their contents to the public repository.
- Never include private context in generated files, logs, pull requests, or commit messages without explicit authorization.
- Request confirmation before modifying files in the separate `career-context` repository.

The career context may be read locally for authorized tasks, but its contents must not be published.

## application development

when working on the streamlit application:

- follow the existing project structure and conventions.
- prefer maintainable, readable python code.
- add or update tests for relevant changes.
- avoid introducing unnecessary dependencies or complexity.
- keep application development independent from private career-context storage unless explicitly requested.