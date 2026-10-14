# TrainTrack Home Assistant Integration

Custom integration for connecting Home Assistant to TrainTrack.

The integration polls the authenticated user's monitored connections and creates three sensors per connection:

- **Status** with the current monitoring status
- **Zug** with the matched train identifier
- **Verspätung** with the reported delay in minutes

Each sensor also exposes the route, weekday or service date, monitor details, observations, and available history as attributes. New connections appear after the next poll. API outages mark entities unavailable; a revoked API key opens Home Assistant's reauthentication flow.

## Configure the integration

1. Sign in to TrainTrack through its SSO provider and open **Einstellungen → API-Schlüssel**.
2. Create a key named **Home Assistant** and copy the value shown once.
3. In Home Assistant, add the **TrainTrack** integration and enter the public HTTPS URL of your TrainTrack instance, the API key, and an initial polling interval.

The API key is stored in the Home Assistant config entry and grants read-only access to your account's session identity and connections. TrainTrack stores only its hash. Keep the URL on HTTPS; plain HTTP is accepted only for localhost during local development. You can change the polling interval later in Home Assistant's integration options (30–3600 seconds, in 30-second steps). If a key is revoked, Home Assistant asks for a replacement.

This integration is read-only. It does not create, update, delete, or select TrainTrack connections.

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

Run the integration tests locally with `python -m unittest discover -s tests -v`. Pull requests and pushes run the test suite, HACS repository validator, and Home Assistant's `hassfest` validator. Pushes also upload Python coverage to SonarQube and wait for its Quality Gate. The project key is stored in `sonar-project.properties`; configure only `SONAR_HOST_URL` and `SONAR_TOKEN` as GitHub repository secrets.

## Versioning and releases

Every commit adds its user-visible change under `Unreleased` in `CHANGELOG.md`. Each push advances the version and moves all accumulated `Unreleased` entries into the next version's changelog section. Unless the user explicitly requests a release, pushed versions are marked as development versions and do not publish a final release. Major version bumps require explicit user approval. See `AGENTS.md` for the repository contribution rules.
