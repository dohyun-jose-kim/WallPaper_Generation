# Local macOS ARM64 installation

No installer release has been published. After completing [source setup](../README.md#quick-start-from-source), build a local bundle from the repository root:

```sh
.venv/bin/python scripts/build-release.py
```

This creates ignored `dist/wall-e-macos-arm64/` with the Rust executable, a bundled Python runtime, engine and dependency wheels, matching Chromium, browser assets, configuration, locks, and upstream notices. The build needs network access to acquire locked dependencies that are not cached. Once built, installation uses the bundle offline. The manifest records SHA-256 hashes and symlink targets; built wheels have installation hashes.

## Install and run

Choose an installation directory separate from your photo workspace. Run these commands in the same terminal, from the repository root:

```sh
WALLE_BUNDLE="$PWD/dist/wall-e-macos-arm64"
WALLE_PREFIX="$HOME/Applications/WALL-E"
WALLE_WORKSPACE="$HOME/Pictures/WALL-E"

# Preview installation locations and dependencies; no installation writes
"$WALLE_BUNDLE/install.sh" install --prefix "$WALLE_PREFIX"

# Apply the displayed plan
"$WALLE_BUNDLE/install.sh" install --prefix "$WALLE_PREFIX" --yes

WALLE_BIN="$WALLE_PREFIX/current/bin/wall-e"
"$WALLE_BIN" --version
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" init
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" doctor
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" render "/absolute/path/to/photo.png" --preset FHD
```

The Python environment is created at its final version path. The installer validates Chromium/WebGL, SQLite, and monitoring before activation. Installed users do not need separate Python, Rust, Node.js, npm, or uv installations.

To request an optional launcher, add `--launcher /absolute/existing-folder/wall-e` to the installation command. The launcher parent directory must already exist, and an existing launcher is never overwritten. The installer does not edit PATH or shell profiles; a launcher is available as `wall-e` only if its directory is already on your PATH. Otherwise, invoke its full path or use `WALLE_BIN` as above.

## Upgrade, rollback, and uninstall

For an upgrade, set `WALLE_BUNDLE` to the new bundle's directory and use the same installation prefix:

```sh
"$WALLE_BUNDLE/install.sh" upgrade --prefix "$WALLE_PREFIX" --yes
```

Every bundle hash is verified. A new version is installed and checked before `current` switches atomically. Previous versions are retained for rollback.

```sh
"$WALLE_BUNDLE/install.sh" rollback --prefix "$WALLE_PREFIX" --yes
"$WALLE_BUNDLE/install.sh" uninstall --prefix "$WALLE_PREFIX" --yes
```

These are separate operations: run the one you need. Rollback checks the preceding environment before activating it. Uninstall removes recorded application files and an unchanged owned launcher. Photo workspaces and unrecorded files are preserved. Omitting `--yes` previews any operation.

If the original bundle is no longer available, the installed manager can also be invoked directly. For example:

```sh
"$WALLE_PREFIX/current/python/bin/python3.12" \
  "$WALLE_PREFIX/current/manage.py" uninstall --prefix "$WALLE_PREFIX" --yes
```

## Installation verification

From the source checkout, run:

```sh
.venv/bin/python tests/integration/check_install.py
```

The test creates disposable installation prefixes and workspaces outside the repository, with spaces in their paths. It checks installation, real rendering, upgrade, rejected corrupt upgrades, rollback, and uninstall with workspace preservation. Runtime PATH is restricted to `/usr/bin:/bin`.

These artifacts are local development builds and are not signed or notarized releases. Building a bundle does not publish it, create a GitHub Release, or create a Git tag. Ordinary macOS process-monitoring and browser-launch access is required.
