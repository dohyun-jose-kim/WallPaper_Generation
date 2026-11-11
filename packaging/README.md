# Managed macOS ARM64 installation

Build locally with `.venv/bin/python scripts/build-release.py`. It creates ignored `dist/wall-e-macos-arm64/`, containing a compiled Rust executable, relocatable Python, engine and dependency wheels, matching Chromium, production browser assets, configuration, locks and upstream notices. The manifest records SHA-256 and symlink targets; built wheels receive installation hashes. No upload, release or tag occurs.

Choose a prefix separate from your photo workspace. Preview writes and dependencies:

```sh
./dist/wall-e-macos-arm64/install.sh install --prefix "$HOME/Applications/WALL-E"
```

Apply the displayed plan by adding `--yes`. Request a launcher only with `--launcher /absolute/existing-folder/wall-e`. Existing launchers are never overwritten; PATH and shell profiles are not changed. Without a launcher, run `PREFIX/current/bin/wall-e`.

Upgrade using the new bundle's `install.sh upgrade --prefix PREFIX --yes`. It verifies every bundle hash, creates the Python environment at its final version path, installs wheels offline, and launches real Chromium/WebGL plus SQLite/monitor checks before switching `current` atomically. Previous versions are retained.

Rollback: `install.sh rollback --prefix PREFIX --yes`; the previous environment is checked before activation. Uninstall: `install.sh uninstall --prefix PREFIX --yes`. Only recorded application files and an unchanged owned launcher are removed. Workspaces and unrecorded files survive. The installed manager is also available at `PREFIX/current/manage.py`, executed with `PREFIX/current/python/bin/python3.12`.

Run `.venv/bin/python tests/integration/check_install.py` for an actual install/render/upgrade/rollback/uninstall test in disposable prefixes outside the repository with spaces. Runtime tests restrict PATH to `/usr/bin:/bin`.

Artifacts are local development builds, not signed/notarized distribution releases. Publication and release tags are deferred. macOS process-monitoring and browser-launch permissions are needed; restricted execution environments fail closed.
