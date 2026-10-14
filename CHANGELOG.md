# Changelog

Changes are recorded here. Every commit adds a concise entry to `Unreleased`.

## Unreleased

## 0.2.3-dev.1 (Development)

- Prepare the development push and carry forward all accumulated unreleased changes.

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
