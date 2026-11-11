#!/usr/bin/env python3
"""Managed, offline install/upgrade/rollback/uninstall. Workspaces are never owned."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import tempfile

MARKER='.wall-e-install.json'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def relative_path(root,name):
    relative=Path(name)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        raise ValueError('Invalid manifest path')
    return root/relative


def verify(bundle):
    manifest=json.loads((bundle/'manifest.json').read_text())
    expected_id=hashlib.sha256(json.dumps({k:v for k,v in manifest.items() if k!='build_id'},sort_keys=True).encode()).hexdigest()[:16]
    if manifest.get('build_id')!=expected_id:raise ValueError('Manifest ID mismatch')
    if manifest['schema_version']!=1 or manifest['platform']!='macos-arm64':
        raise ValueError('Unsupported manifest')
    for name,expected in manifest['files'].items():
        path=relative_path(bundle,name)
        if path.is_symlink() or digest(path)!=expected:raise ValueError('Bundle hash mismatch')
    for name,target in manifest['symlinks'].items():
        path=relative_path(bundle,name)
        if not path.is_symlink() or os.readlink(path)!=target or not path.resolve().is_relative_to(bundle):
            raise ValueError('Bundle symlink mismatch')
    allowed=set(manifest['files'])|set(manifest['symlinks'])|{'manifest.json'}
    if any(p.relative_to(bundle).as_posix() not in allowed for p in bundle.rglob('*') if p.is_file() or p.is_symlink()):
        raise ValueError('Unexpected bundle files')
    return manifest


def atomic_json(path,value):
    temp=path.with_name(path.name+'.new')
    with temp.open('x') as file:
        json.dump(value,file,indent=2);file.write('\n');file.flush();os.fsync(file.fileno())
    os.replace(temp,path)


def activate(prefix,build):
    current=prefix/'current'
    if current.exists() and not current.is_symlink():raise ValueError('Activation path is not owned')
    temp=prefix/'.current-new'
    temp.symlink_to(Path('versions')/build)
    os.replace(temp,current)


def inventory(root):
    return [p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() or p.is_symlink()]


def remove_owned(root,files):
    # Only recorded files are removed. New files and user workspaces survive.
    for name in sorted(files,key=lambda s:len(Path(s).parts),reverse=True):
        path=relative_path(root,name)
        if any(p.is_symlink() for p in path.parents if p!=root and p.is_relative_to(root)):
            continue
        if path.is_file() or path.is_symlink():path.unlink()
    parents={parent for name in files for parent in relative_path(root,name).parents if parent!=root and parent.is_relative_to(root)}
    for path in sorted(parents,key=lambda p:len(p.parts),reverse=True):
        if path.is_dir() and not path.is_symlink():
            with contextlib.suppress(OSError):path.rmdir()
    with contextlib.suppress(OSError):root.rmdir()


def doctor(version):
    with tempfile.TemporaryDirectory(prefix='wall-e-install-check-') as work:
        env={**os.environ,'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'}
        env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
        subprocess.run([str(version/'bin/wall-e'),'--workspace',work,'doctor'],env=env,check=True,timeout=150)


def install(bundle,prefix,launcher,state):
    manifest=verify(bundle);build=manifest['build_id']
    if not build.isalnum():raise ValueError('Invalid build ID')
    versions=prefix/'versions';versions.mkdir(exist_ok=True)
    if versions.is_symlink():raise ValueError('Version directory must not be a symlink')
    version=versions/build
    if version.exists():raise ValueError('This build is already installed')
    launcher_text=None
    if launcher:
        launcher_text='#!/bin/sh\nexec '+shlex.quote(str(prefix/'current/bin/wall-e'))+' "$@"\n'
        if launcher.exists() or launcher.is_symlink():raise ValueError('Launcher path already exists')
        if not launcher.parent.is_dir():raise ValueError('Launcher parent does not exist')
    if state.get('launcher') and launcher:raise ValueError('Installation already has a launcher')
    marker_written=False
    launcher_written=False
    try:
        shutil.copytree(bundle,version,symlinks=True)
        # Create the venv at its final path; do not relocate an existing venv.
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PIP_DISABLE_PIP_VERSION_CHECK':'1','PIP_NO_CACHE_DIR':'1'}
        env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
        python=version/'python/bin/python3.12'
        subprocess.run([str(python),'-m','venv',str(version/'env')],env=env,check=True)
        subprocess.run([str(version/'env/bin/python'),'-m','pip','install','--no-index','--no-deps','--require-hashes','-r','install-requirements.txt'],cwd=version,env=env,check=True)
        doctor(version)
        owned=inventory(version)
        previous=state.get('current')
        updated={**state,'schema_version':1,'current':build,'previous':previous,
                 'versions':{**state.get('versions',{}),build:owned}}
        if launcher:
            with launcher.open('x') as file:file.write(launcher_text)
            launcher.chmod(0o755);launcher_written=True;updated['launcher']={'path':str(launcher),'content':launcher_text}
        # Journal intent before pointer activation; startup reconciles the actual pointer.
        atomic_json(prefix/MARKER,updated)
        marker_written=True
        activate(prefix,build)
        return updated
    except Exception:
        if not (prefix/'current').is_symlink() or (prefix/'current').resolve()!=version:
            shutil.rmtree(version,ignore_errors=True)
            if marker_written:
                if state:atomic_json(prefix/MARKER,state)
                else:(prefix/MARKER).unlink(missing_ok=True)
            if launcher_written and launcher.read_text()==launcher_text:launcher.unlink()
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['install','upgrade','rollback','uninstall'])
    parser.add_argument('--prefix',type=Path,required=True)
    parser.add_argument('--launcher',type=Path)
    parser.add_argument('--yes',action='store_true',help='Apply the displayed plan')
    args=parser.parse_args()
    if (platform.system(),platform.machine())!=('Darwin','arm64'):parser.error('macOS ARM64 required')
    prefix=args.prefix.expanduser().absolute().resolve()
    launcher=args.launcher.expanduser().absolute() if args.launcher else None
    if launcher and args.action not in ('install','upgrade'):parser.error('Launcher is an install option')
    print(f'Action: {args.action}\nInstallation directory: {prefix}\nVersion files: {prefix}/versions\nActivation pointer: {prefix}/current\nDependencies: bundled Python 3.12, locked wheels, matching Chromium; offline installation.\nLauncher: {launcher or "none requested"}\nPATH and shell profiles: unchanged\nPhoto workspaces: separate; preserved',flush=True)
    if not args.yes:return
    os.umask(0o077)
    if not prefix.exists():
        if args.action!='install':raise ValueError('Installation not found')
        prefix.mkdir(parents=True)
    marker=prefix/MARKER
    if marker.is_symlink():raise ValueError('Installation marker cannot be a symlink')
    state=json.loads(marker.read_text()) if marker.exists() else {}
    if state:
        for build in state.get('versions',{}):
            if not build.isalnum():raise ValueError('Invalid installed version')
        current=prefix/'current'
        if current.is_symlink():
            actual=Path(os.readlink(current))
            if len(actual.parts)!=2 or actual.parts[0]!='versions' or actual.parts[1] not in state['versions']:raise ValueError('Unowned activation pointer')
            # Recover a crash between journal update and atomic activation.
            if state['current']!=actual.parts[1]:
                state['previous']=state['current'];state['current']=actual.parts[1]
    if args.action=='install' and state:raise ValueError('Use upgrade for an existing installation')
    if args.action!='install' and not state:raise ValueError('Installation not found')
    if not state and any((prefix/name).exists() or (prefix/name).is_symlink() for name in ['versions','current','.install.lock']):raise ValueError('Installation paths already exist and are not owned')
    lock_path=prefix/'.install.lock'
    if lock_path.is_symlink():raise ValueError('Lock cannot be a symlink')
    with lock_path.open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.action in ('install','upgrade'):
            install(Path(__file__).resolve().parent,prefix,launcher,state)
        elif args.action=='rollback':
            previous=state.get('previous')
            if not previous or previous not in state['versions']:raise ValueError('No previous installation')
            doctor(prefix/'versions'/previous)
            state['current'],state['previous']=previous,state['current']
            atomic_json(marker,state);activate(prefix,previous)
        else:
            link=prefix/'current'
            if link.is_symlink() and os.readlink(link)==str(Path('versions')/state['current']):link.unlink()
            for build,files in state['versions'].items():
                remove_owned(prefix/'versions'/build,files)
            with contextlib.suppress(OSError):(prefix/'versions').rmdir()
            launch=state.get('launcher')
            if launch:
                path=Path(launch['path'])
                if path.is_file() and not path.is_symlink() and path.read_text()==launch['content']:path.unlink()
            marker.unlink();lock_path.unlink()
    if args.action=='uninstall':
        with contextlib.suppress(OSError):prefix.rmdir()
    print(f'{args.action.capitalize()} completed.')

if __name__=='__main__':main()
