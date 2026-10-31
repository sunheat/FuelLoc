# FuelLoc code review standards

FuelLoc is a personal, locally run Windows utility used with the owner's own iPhone. Review changes against that scope and the stated request. Prioritize reproducible problems that would break startup, packaging, device connection, location control, data integrity, or the local web security boundary.

- Report a finding only when there is a concrete failure path in the changed code. Include the triggering condition and user-visible impact.
- Treat a missing Apple service, disconnected phone, disabled Developer Mode, absent browser, and unavailable Internet as expected environmental states. The prerequisite screen may report them while still allowing entry.
- Do not require SaaS-style concerns such as multi-user isolation, cloud deployment, high availability, telemetry, enterprise configuration, or exhaustive hypothetical edge-case handling.
- Keep validation at HTTP and device trust boundaries. Do not suggest weakening origin checks, coordinate validation, or license obligations for simplicity.
- Prefer small, direct fixes and existing Python or Windows facilities over new frameworks or abstractions.
- Preserve GPLv3 license text and minimal upstream attribution. Do not reintroduce the original author's donation, survey, community, repository, or affiliate links into the app.

These standards set review priority; they do not waive concrete defects or explicit requirements.

## Agent skills

The configuration files below are local to this checkout and must not be
committed or published. If they are absent, ask the user to configure the
skills locally before tracker-dependent work. Do not infer a tracker from
another repository.

### Issue tracker

Use the locally configured issue tracker. See `docs/agents/issue-tracker.md`.

### Domain docs

Use a single-context layout with root `CONTEXT.md` and `docs/adr/`.
See `docs/agents/domain.md`.
