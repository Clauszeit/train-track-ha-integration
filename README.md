# TrainTrack Home Assistant Integration

Custom integration for connecting Home Assistant to TrainTrack.

The repository currently contains the initial integration scaffold. Runtime behavior and supported TrainTrack API capabilities will be documented here as they are implemented.

## Repository layout

- `custom_components/traintrack/`: Home Assistant integration
- `tests/`: integration tests
- `.github/workflows/`: repository validation workflows
- `VERSION`: central project version
- `CHANGELOG.md`: committed changes and release history

## Validation

Pull requests and pushes run the Home Assistant `hassfest` validator. Add focused tests alongside functional changes and run the repository's test command before committing.

## Versioning and releases

Every commit adds its user-visible change under `Unreleased` in `CHANGELOG.md`. Each push advances the version and moves all accumulated `Unreleased` entries into the next version's changelog section. Unless the user explicitly requests a release, pushed versions are marked as development versions and do not publish a final release. Major version bumps require explicit user approval. See `AGENTS.md` for the repository contribution rules.
