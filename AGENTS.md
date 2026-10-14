# Contribution and coding-agent instructions

## Project goal

Provide a Home Assistant custom integration for TrainTrack. Use documented, supported TrainTrack interfaces and Home Assistant APIs. Do not invent endpoint behavior or rely on unofficial third-party services.

## Required practices

- Read existing files and preserve user data before making changes.
- Keep secrets, private configuration, credentials, and user data out of Git. Maintain `.gitignore` and safe example configuration.
- Keep documentation and `CHANGELOG.md` current for functional changes.
- Every commit adds its change under `Unreleased` in `CHANGELOG.md`. Every push advances the version and moves all accumulated unreleased entries into the next version's changelog section. Unless the user explicitly requests a release, pushed versions are marked as development versions and must not create a final release.
- Major version bumps require explicit user approval. Automation must stop before applying a major bump unless that approval is present.
- Keep the central version in `VERSION`, the integration manifest version, visible version strings, and release tags consistent. Git release tags use `vX.Y.Z`.
- Each new behavior needs focused functional and regression tests. Run all available local tests before every commit. If no applicable test system exists yet, record that limitation rather than inventing a test run.
- Before and after changes, query the connected SonarQube MCP for the Quality Gate, open issues, and coverage requirements; repeat these checks after a push until the server reflects the pushed revision. If the project is not yet connected or the MCP cannot report the working revision, record that limitation and identify server results as the last analyzed state.
- Check the effects of changes across integration code, API contracts, configuration flow, translations, documentation, CI, and release packaging. Update affected parts together.
- Keep commits focused on one coherent topic. Stage and commit only files for that topic; preserve unrelated user changes and pre-staged changes.
- Do not publish or deploy without an explicit request.
- Report what changed and what remains unverified.

## Home Assistant integration

- Keep the integration under `custom_components/traintrack/`, describe it in the root `hacs.json`, and validate it with both the HACS action and Home Assistant's `hassfest` workflow.
- Use only documented Home Assistant interfaces and the official TrainTrack API.
- Treat unavailable API responses and authentication errors as recoverable integration states; avoid exposing credentials in logs.
