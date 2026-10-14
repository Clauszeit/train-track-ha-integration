# Publishing and updates

## Current distribution

TrainTrack is a public GitHub repository that users add to HACS as a **custom repository** with category **Integration**. It is not currently included in the HACS default catalog. HACS installs the integration files from the repository; this project does not publish a Home Assistant add-on, container image, or packaged build.

The `main` branch is the development channel. A push to `main` updates the files available through HACS after the user checks for and installs the update, then restarts Home Assistant. The current repository has no Git tags or GitHub Releases. In this state, HACS uses the default branch and identifies it by the latest commit; the `VERSION` and manifest values describe the integration build but do not themselves create a HACS release.

## What CI does

`.github/workflows/validate.yml` runs on pushes, pull requests, a weekly schedule, and manual dispatch. It runs the HACS repository validator and Home Assistant `hassfest` validator. On non-pull-request runs it also runs the integration tests with coverage and uploads the result to SonarQube, waiting for its Quality Gate. Configure `SONAR_HOST_URL` and `SONAR_TOKEN` as repository secrets.

CI does **not** bump versions, move changelog entries, create Git tags, create GitHub Releases, or publish an archive. Version and changelog changes must be prepared in the repository before the development push. A successful validation run only means the source passed its configured checks; it does not mean a final release was published.

## Preparing a development push

1. Add each user-visible change under `Unreleased` in `CHANGELOG.md` and run the local tests with `python -m unittest discover -s tests -v`.
2. Before pushing the completed change, choose the next development version. Before `1.0.0`, use `0.x.0` for a feature and increment the patch for a fix. Do not bump the major version without explicit approval.
3. Move the accumulated `Unreleased` entries into a new `X.Y.Z-dev.N (Development)` section in `CHANGELOG.md`. Keep `Unreleased` ready for later work.
4. Set the same development version in `VERSION` and `custom_components/traintrack/manifest.json`.
5. Commit the version and changelog changes with the implementation and push to `main`. Check the `Validate` workflow and SonarQube result after the push.

This updates the development channel only. It does not publish a final release or create a Git tag.

## Publishing a final release

Create a final release only after it has been explicitly requested and approved.

1. Confirm the intended version and ensure CI and SonarQube pass on the exact `main` commit.
2. Remove the development suffix and set the final `X.Y.Z` version in `VERSION` and the integration manifest. Add a matching `X.Y.Z` section to `CHANGELOG.md` and clear the entries moved from `Unreleased`.
3. Commit and push the release version. Wait for the validation workflow to succeed.
4. Create and push an annotated Git tag named `vX.Y.Z` at that validated commit.
5. Create a **published GitHub Release** for that tag and use the matching changelog entries as its release notes. A tag without a published GitHub Release is not a HACS release.

The tag must match the version files, and release tags use the `vX.Y.Z` format. HACS can offer published GitHub releases alongside the default branch; without a GitHub Release it continues to install from the default branch. See the [HACS integration publishing documentation](https://www.hacs.dev/docs/publish/integration/) and [HACS version documentation](https://www.hacs.dev/docs/publish/start/#versions).
