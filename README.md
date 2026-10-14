# TrainTrack Home Assistant Integration

Custom integration for connecting Home Assistant to TrainTrack.

The repository currently contains the initial integration scaffold. Runtime behavior and supported TrainTrack API capabilities will be documented here as they are implemented.

## Install through HACS

In HACS, open the menu, choose **Custom repositories**, add `https://github.com/Clauszeit/train-track-ha-integration` as an **Integration**, then install **TrainTrack**. The repository must be public for HACS to access it.

Until an explicit release is requested, HACS uses the default branch. Normal pushes are development versions; published GitHub releases are reserved for explicitly requested releases.

## Repository layout

- `custom_components/traintrack/`: Home Assistant integration
- `tests/`: integration tests
- `.github/workflows/`: repository validation workflows
- `VERSION`: central project version
- `CHANGELOG.md`: committed changes and release history

## Validation

Pull requests and pushes run the HACS repository validator and Home Assistant's `hassfest` validator. Pushes also run SonarQube analysis. Configure `SONAR_HOST_URL`, `SONAR_PROJECT_KEY`, and `SONAR_TOKEN` as GitHub repository secrets; none of these values belong in tracked files. Add focused tests alongside functional changes and run the repository's test command before committing.

## Versioning and releases

Every commit adds its user-visible change under `Unreleased` in `CHANGELOG.md`. Each push advances the version and moves all accumulated `Unreleased` entries into the next version's changelog section. Unless the user explicitly requests a release, pushed versions are marked as development versions and do not publish a final release. Major version bumps require explicit user approval. See `AGENTS.md` for the repository contribution rules.
