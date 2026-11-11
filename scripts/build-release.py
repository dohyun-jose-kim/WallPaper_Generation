#!/usr/bin/env python3
"""Assemble a local macOS ARM64 distribution. Does not publish or tag."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/'Photo-to-Wallpaper-Rendering-Engine'
SHELF=ENGINE/'tool-package-shelf'
OUT=ROOT/'dist/wall-e-macos-arm64'


def run(*args, **kwargs):
    subprocess.run([str(a) for a in args],check=True,**kwargs)


def main():
    if (platform.system(),platform.machine())!=('Darwin','arm64'):
        raise SystemExit('Build requires macOS ARM64')
    run(ROOT/'scripts/cargo.sh','build','--release','--locked')
    run('node',SHELF/'build-production.mjs')
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    env={**os.environ,'UV_CACHE_DIR':str(ROOT/'.wallpaper/uv-cache'),'PYTHONDONTWRITEBYTECODE':'1','PIP_CACHE_DIR':str(ROOT/'.wallpaper/pip-cache')}
    run('uv','build','--wheel','--no-build-isolation','--python',ROOT/'.venv/bin/python','--out-dir',OUT/'wheels',ENGINE,env=env)
    shutil.copytree(Path(sys.base_prefix),OUT/'python',symlinks=True)
    # Built artifacts retain their upstream notices. No editable installs or repository paths.
    builder=ROOT/'.wallpaper/build-env'
    run(OUT/'python/bin/python3.12','-m','venv',builder,env=env)
    run(builder/'bin/python','-m','pip','install','--require-hashes','-r',SHELF/'requirements-build.lock',env=env)
    wheels=OUT/'wheels';wheels.mkdir(exist_ok=True)
    run(builder/'bin/python','-m','pip','wheel','--no-deps','--require-hashes','--no-build-isolation',
        '--wheel-dir',wheels,'-r',SHELF/'requirements.lock',env=env)
    shutil.copytree(SHELF/'browser-binaries',OUT/'browsers',symlinks=True,ignore=shutil.ignore_patterns('.links'))
    (OUT/'bin').mkdir();shutil.copy2(ROOT/'orchestrator/target/release/wall-e',OUT/'bin/wall-e')
    shutil.copytree(ROOT/'config',OUT/'config')
    shutil.copytree(SHELF/'licenses',OUT/'licenses')
    shutil.copy2(SHELF/'ATTRIBUTION.md',OUT/'ATTRIBUTION.md')
    for lock in ['requirements.lock','requirements-build.lock','package-lock.json','source-manifest.json']:
        shutil.copy2(SHELF/lock,OUT/lock)
    shutil.copy2(ROOT/'orchestrator/Cargo.lock',OUT/'Cargo.lock')
    for package in ['react','react-dom']:
        shutil.copy2(SHELF/'node_modules'/package/'LICENSE',OUT/'licenses'/f'{package}-LICENSE')
    shutil.copy2(ROOT/'packaging/manage.py',OUT/'manage.py')
    shutil.copy2(ROOT/'packaging/install.sh',OUT/'install.sh')
    # Wheel-built dependencies are authenticated here; the source distributions remain pinned above.
    requirements=[]
    for wheel in sorted(wheels.glob('*.whl')):
        requirements.append(f'./wheels/{wheel.name} --hash=sha256:{hashlib.sha256(wheel.read_bytes()).hexdigest()}')
    (OUT/'install-requirements.txt').write_text('\n'.join(requirements)+'\n')
    files={};links={}
    for p in sorted(OUT.rglob('*')):
        relative=p.relative_to(OUT).as_posix()
        if p.is_symlink():
            target=os.readlink(p)
            if not p.resolve().is_relative_to(OUT.resolve()): raise RuntimeError(f'External symlink in distribution: {relative}')
            links[relative]=target
        elif p.is_file():files[relative]=hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'schema_version':1,'version':'0.1.0','platform':'macos-arm64','python':'3.12.14','files':files,'symlinks':links}
    manifest['build_id']=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()[:16]
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(OUT)

if __name__=='__main__':main()
