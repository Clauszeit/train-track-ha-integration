# Changelog

Changes are recorded here. Every commit adds a concise entry to `Unreleased`.

## Unreleased

- Expose linked alternative connections, both delay thresholds, and current switch/earlier-connection recommendations on connection sensor attributes.

## 0.5.5-dev.1 (Development)

- Replace long route-based sensor IDs with stable purpose-first IDs and migrate repeated schedule fragments, including truncated and suffixed IDs.

## 0.5.4-dev.1 (Development)

- Ship runtime English and German translations so the device page shows distinct Status, Train/Zug, and Delay/Verspätung sensor names.

## 0.5.3-dev.1 (Development)

- Normalize Home Assistant entity IDs when repeated schedule names accumulated in the registry.
- Log when a monitored connection disappears from or reappears in a successful API response.
- Fix the options flow crashing when Home Assistant loads its configuration form.

## 0.5.2-dev.1 (Development)

- Fix Home Assistant entity cleanup to use the supported entity registry helper.

## 0.5.1-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Reduce the sensor setup function's SonarQube cognitive complexity without changing integration behavior.
- Migrate legacy route-only entity IDs and remove expired one-time trip devices after a configurable retention period.
- Refresh automatically managed Home Assistant device names in the registry and preserve names set by users.
- Use the main TrainTrack logo for Home Assistant branding.

## 0.5.0-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Migrate legacy route-only entity IDs and remove expired one-time trip devices after a configurable retention period.
- Refresh automatically managed Home Assistant device names in the registry and preserve names set by users.
- Use the main TrainTrack logo for Home Assistant branding.

## 0.4.3-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Refresh automatically managed Home Assistant device names in the registry and preserve names set by users.

## 0.4.2-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Add a complete reference for Home Assistant devices, sensors, names, states, attributes, histories, and availability.

## 0.4.1-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Document the actual HACS development channel, CI behavior, version preparation, and final release steps.
- Correct the invalid URL message to match support for user-configured HTTP and HTTPS addresses.

## 0.4.0-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Include scheduled times in device names and expose complete schedule and monitoring details on entities.

## 0.3.4-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Allow user-configured HTTP and HTTPS server URLs for different network layouts.

## 0.3.3-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Allow the documented `http://webserver:8080` endpoint for Home Assistant instances on the same trusted Docker network.

## 0.3.2-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Korrigiert die Sonar-Suppressionssyntax für erforderliche asynchrone Home-Assistant-Hooks.

## 0.3.1-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Fix SonarQube findings and add functional coverage for the API client, config flow, polling coordinator, migrations, and sensors.

## 0.3.0-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.
- Use revocable read-only TrainTrack API keys instead of browser SSO cookies and make the connection polling interval configurable in Home Assistant.
- Implement the Home Assistant config flow, authenticated TrainTrack API polling, and per-connection status, train, and delay sensors with route and history attributes.

## 0.2.4-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.

- Pinnt alle Workflow-Jobs auf `ubuntu-24.04`, damit der angekündigte Wechsel von `ubuntu-latest` auf Ubuntu 26 die Validierung nicht unerwartet verändert.
- Aktualisiert Checkout auf v7.0.1 und SonarQube Scan Action auf v8.3.0; HACS Action 22.5.0 ist bereits aktuell. Hassfest folgt der offiziellen `@master`-Referenz, da keine versionierten Releases angeboten werden.

## 0.2.3-dev.1 (Development)

- Sort Home Assistant manifest keys with `domain` and `name` first and all remaining keys alphabetically for hassfest.

## 0.2.2-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.

- Run SonarQube analysis even when HACS or hassfest fails, then report all prerequisite and Sonar results in one final failing quality gate.

## 0.2.1-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.

- Fail the SonarQube quality gate with the HACS and hassfest job results when either validation fails.

## 0.2.0-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.

- Add HACS metadata, installation instructions, and automated HACS, Home Assistant, and SonarQube validation.
- Store the SonarQube project key in `sonar-project.properties`; keep the host URL and access token in repository secrets.
- Add the initial Home Assistant integration repository scaffold, contribution rules, and Home Assistant validation workflow.
