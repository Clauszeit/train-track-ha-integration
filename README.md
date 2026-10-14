# TrainTrack Home Assistant Integration

Custom integration for connecting Home Assistant to TrainTrack.

The integration polls the authenticated user's monitored connections and creates three sensors per connection:

- **Status** with the current monitoring status
- **Zug** with the matched train identifier
- **Verspätung** with the reported delay in minutes

Each connection device includes the scheduled departure time in its name; recurring services also show weekdays, one-time services show their date, and grouped legs show their position. On the device page, the three sensors are labeled Status, Train, and Delay (Status, Zug, and Verspätung in German). Sensors expose the full API connection data plus readable attributes for scheduled arrival times, connection type, transfer details, current monitor message and state, train, delay, operating date, trip, platform, change details, urgency, historical context, observations, and history. New connections appear after the next poll. API outages mark entities unavailable; a revoked API key opens Home Assistant's reauthentication flow.

Sensor entity IDs start with `sensor.traintrack_status_`, `sensor.traintrack_train_`, or `sensor.traintrack_delay_` followed by a stable 16-character identifier. Older automatically generated route IDs, including repeated schedule fragments, are migrated on update. Update any dashboards, templates, or automations that refer to an old generated entity ID; manually renamed IDs are preserved.

The complete device and entity reference documents the naming rules, sensor states, every API and normalized attribute, history structures, optional values, and availability behavior: [Devices and entities](docs/ENTITIES.md).

## Configure the integration

1. Sign in to TrainTrack through its SSO provider and open **Einstellungen → API-Schlüssel**.
2. Create a key named **Home Assistant** and copy the value shown once.
3. In Home Assistant, add the **TrainTrack** integration and enter the URL by which Home Assistant can reach your TrainTrack instance, the API key, and an initial polling interval. For example, when both containers share the default TrainTrack Compose network, use `http://webserver:8080`; for other network layouts, enter the hostname or IP address and port configured for your server.

The API key is stored in the Home Assistant config entry and grants read-only access to your account's session identity and connections. TrainTrack stores only its hash. Both HTTP and HTTPS URLs are supported so the address can match your network. HTTPS protects the API key in transit; use HTTP only on a trusted, isolated network because it sends the key without TLS. You can change the polling interval later in Home Assistant's integration options (30–3600 seconds, in 30-second steps) and set how long completed one-time trips remain in Home Assistant (default: seven days; configurable from one to 365 days). If a key is revoked, Home Assistant asks for a replacement.

This integration is read-only. It does not create, update, delete, or select TrainTrack connections.

## Install through HACS

In HACS, open the menu, choose **Custom repositories**, add `https://github.com/Clauszeit/train-track-ha-integration` as an **Integration**, then install **TrainTrack**. The repository must be public for HACS to access it.

Until an explicit release is requested, HACS uses the default branch. Normal pushes are development versions; published GitHub releases are reserved for explicitly requested releases.

After installing an update, restart Home Assistant so it loads the updated integration and sensor translations. Existing manually assigned entity names remain under your control.

The integration is distributed as a **custom HACS repository** and is not currently listed in the HACS default catalog. The validation workflow checks changes but does not create packages, GitHub releases, or version bumps. See [Publishing and updates](docs/PUBLISHING.md) for the exact development and release process.

## Repository layout

- `custom_components/traintrack/`: Home Assistant integration
- `tests/`: integration tests
- `.github/workflows/`: repository validation workflows
- `VERSION`: central project version
- `CHANGELOG.md`: committed changes and release history

## Validation

Run the integration tests locally with `python -m unittest discover -s tests -v`. Pull requests and pushes run the test suite, HACS repository validator, and Home Assistant's `hassfest` validator. Pushes also upload Python coverage to SonarQube and wait for its Quality Gate. The project key is stored in `sonar-project.properties`; configure only `SONAR_HOST_URL` and `SONAR_TOKEN` as GitHub repository secrets.

## Versioning and releases

Use the documented [publishing process](docs/PUBLISHING.md) to prepare the development version before pushing or to create a final release after it has been explicitly approved. Major version bumps require explicit user approval. See `AGENTS.md` for the repository contribution rules.
