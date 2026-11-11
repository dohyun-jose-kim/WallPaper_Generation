"""Full offline lifecycle check in disposable prefixes outside the repository."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
BUNDLE=ROOT/'dist/wall-e-macos-arm64'
ENV={**os.environ,'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'}
ENV.pop('PYTHONPATH',None);ENV.pop('PYTHONHOME',None)


def run(bundle,*args,success=True):
    result=subprocess.run([str(bundle/'install.sh'),*map(str,args)],env=ENV,text=True,capture_output=True,timeout=180)
    assert (result.returncode==0)==success,(result.stdout,result.stderr)
    return result


def rehash(bundle):
    manifest=json.loads((bundle/'manifest.json').read_text())
    for name in manifest['files']:
        manifest['files'][name]=hashlib.sha256((bundle/name).read_bytes()).hexdigest()
    manifest.pop('build_id',None)
    manifest['build_id']=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()[:16]
    (bundle/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


def main():
    with tempfile.TemporaryDirectory(prefix='WALL-E lifecycle ') as temporary:
        root=Path(temporary);prefix=root/'application prefix';launcher=root/'wall-e launcher'
        run(BUNDLE,'install','--prefix',prefix)
        assert not prefix.exists(), 'Plan-only install must not write'
        run(BUNDLE,'install','--prefix',prefix,'--launcher',launcher,'--yes')
        first=(prefix/'current').resolve();assert first.is_dir() and launcher.exists()
        workspace=root/'photo workspace';source=root/'source.png'
        from PIL import Image
        Image.new('RGB',(83,61),(80,130,200)).save(source)
        subprocess.run([str(launcher),'--workspace',str(workspace),'render',str(source),'--width','512','--height','512'],env=ENV,check=True,timeout=120)
        outputs=sorted((workspace/'wall-pic-out').glob('*/*/*.png'));assert len(outputs)==4
        hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}
        # A new build with unchanged engines still exercises activation and rollback.
        second_bundle=root/'second bundle';shutil.copytree(BUNDLE,second_bundle,symlinks=True)
        with (second_bundle/'ATTRIBUTION.md').open('a') as file:file.write('\nLifecycle test build.\n')
        rehash(second_bundle)
        run(second_bundle,'upgrade','--prefix',prefix,'--yes')
        second=(prefix/'current').resolve();assert second!=first and first.is_dir()
        # Corrupt candidate cannot replace the active installation.
        with (second_bundle/'config/defaults.json').open('a') as file:file.write('corrupt')
        run(second_bundle,'upgrade','--prefix',prefix,'--yes',success=False)
        assert (prefix/'current').resolve()==second
        run(BUNDLE,'rollback','--prefix',prefix,'--yes')
        assert (prefix/'current').resolve()==first
        assert second.is_dir()
        # Never claim a workspace or an unrecorded file as application ownership.
        keep=prefix/'user-note.txt';keep.write_text('preserve')
        nested=second/'user-note.txt';nested.write_text('preserve nested')
        run(BUNDLE,'uninstall','--prefix',prefix,'--yes')
        assert not launcher.exists() and not (prefix/'current').exists()
        assert keep.read_text()=='preserve' and nested.read_text()=='preserve nested'
        assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in hashes.items())
        print('Install, runtime render without developer PATH, validated upgrade, failed-upgrade preservation, rollback, owned-file uninstall, and workspace preservation passed.')

if __name__=='__main__':main()
