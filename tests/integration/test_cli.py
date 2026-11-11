"""Real macOS process monitoring and Chromium integration; run outside a restricted sandbox."""
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import time
import sys
import pytest
from PIL import Image, ImageCms

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Photo-to-Wallpaper-Rendering-Engine/src'))
from wallpaper_engine.image_preparation import prepare_pixels, validate_clean_png
from wallpaper_engine.settings import fit_box
BINARY=Path(os.environ.get('WALL_E_TEST_BINARY', ROOT/'orchestrator/target/debug/wall-e'))


def invoke(work,*args,success=0):
    result=subprocess.run([str(BINARY),'--workspace',str(work),*map(str,args)],capture_output=True,text=True,timeout=180)
    assert result.returncode==success,(result.stdout,result.stderr)
    return result


def photo(path,size=(83,61)):
    image=Image.new('RGB',size)
    image.putdata([((x*3)%256,(y*5)%256,(x+y)%256) for y in range(size[1]) for x in range(size[0])])
    profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    exif=Image.Exif();exif[270]='private metadata never log'
    image.save(path,icc_profile=profile,exif=exif)
    return path


def records(work):
    with sqlite3.connect(work/'.wallpaper/state.sqlite') as db:
        return [json.loads(r[0]) for r in db.execute('SELECT record FROM jobs ORDER BY id')]


def output_set(work,size,count=1):
    jobs=records(work);assert len(jobs)==count
    for job in jobs:
        assert job['status']=='complete'
        folder=work/'wall-pic-out'/job['date']/job['id']
        assert sorted(p.name for p in folder.iterdir())==[f"{job['id']}.{i}.png" for i in range(1,5)]
        prepared,details=prepare_pixels(Path(job['source']).read_bytes(),fit_box(*size,job['border']),size)
        rectangle=details['protected_rectangle_xyxy_exclusive']
        for p in folder.glob('*.png'):
            validate_clean_png(p.read_bytes(),size)
            with Image.open(p) as im:
                assert im.size==size and im.mode=='RGB' and not im.info
                assert im.crop(rectangle).tobytes()==prepared.tobytes()
    assert not list((work/'wall-pic-out').glob('*/.*.staging'))
    return jobs


def test_batch_resume_privacy_and_collision(tmp_path):
    source=photo(tmp_path/'sensitive-source-name.png')
    original=source.read_bytes();work=tmp_path/'work space'
    invoke(work,'render',source,source,source,'--width',512,'--height',512)
    jobs=output_set(work,(512,512),3);assert len({j['id'] for j in jobs})==3
    paths=sorted((work/'wall-pic-out').glob('*/*/*.png'));before={str(p):p.read_bytes() for p in paths}
    invoke(work,'resume',*[j['id'] for j in jobs]);assert len(records(work))==3
    assert all(p.read_bytes()==before[str(p)] for p in paths)
    paths[0].write_bytes(b'collision preserved')
    invoke(work,'resume',jobs[0]['id'],success=3)
    assert paths[0].read_bytes()==b'collision preserved'
    logs=''.join(p.read_text() for p in (work/'logs').glob('*.jsonl'))
    assert 'sensitive-source-name' not in logs and str(source) not in logs and 'private metadata' not in logs
    assert source.read_bytes()==original
    source.write_bytes(b'changed')
    invoke(work,'resume',jobs[1]['id'],success=3)


@pytest.mark.parametrize('size,border', [((512,1024),3),((1024,512),20),((512,1536),5),((1536,512),5)])
def test_geometry_boundary_targets(tmp_path,size,border):
    source=photo(tmp_path/'source.png');work=tmp_path/'ws'
    result=invoke(work,'render',source,'--width',size[0],'--height',size[1],'--border',border)
    output_set(work,size)
    assert ('awkward composition' in result.stderr)==(max(size)/min(size)>2)


def test_reference_orientation_and_oversize(tmp_path):
    source=photo(tmp_path/'source.png');reference=tmp_path/'reference.png'
    exif=Image.Exif();exif[274]=6
    Image.new('RGB',(1024,512)).save(reference,exif=exif)
    work=tmp_path/'ws';invoke(work,'render',source,'--reference',reference);output_set(work,(512,1024))
    Image.new('RGB',(8193,512)).save(reference)
    invoke(tmp_path/'oversize','render',source,'--reference',reference,success=2)
    assert not records(tmp_path/'oversize')


def test_presets_and_invalid_input_continuation(tmp_path):
    source=photo(tmp_path/'source.png');bad=tmp_path/'bad.gif';Image.new('RGB',(3,2)).save(bad)
    work=tmp_path/'ws';invoke(work,'render',bad,source,'--preset','FHD','--swap',success=3)
    output_set(work,(1080,1920))
    for args in [('--width','512','--height','1537'),('--width','8192','--height','8192'),('--border','2')]:
        invoke(tmp_path/'invalid','render',source,*args,success=2)
    invoke(tmp_path/'conflict','render',source,'--preset','FHD','--width','512','--height','512',success=2)


def test_cancel_stops_children_and_cleans_staging(tmp_path):
    source=photo(tmp_path/'source.png');work=tmp_path/'ws'
    process=subprocess.Popen([str(BINARY),'--workspace',str(work),'render',str(source),'--preset','UHD'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    until=time.monotonic()+30
    while time.monotonic()<until:
        if list((work/'wall-pic-out').glob('*/.*.staging')):break
        time.sleep(.03)
    process.send_signal(signal.SIGINT)
    process.communicate(timeout=15);assert process.returncode!=0
    assert not list((work/'wall-pic-out').glob('*/.*.staging'))
    assert all(j['status']!='running' for j in records(work))


def test_settings_and_color_errors_are_explicit(tmp_path):
    work=tmp_path/'ws';invoke(work,'init')
    settings=work/'.wallpaper/settings.json';original=settings.read_bytes()
    settings.write_text('{"brand":"WALL-E","width":"bad","height":1080,"border":0.05}')
    source=photo(tmp_path/'source.png')
    result=invoke(work,'render',source,success=2);assert 'invalid_settings' in result.stderr
    settings.write_bytes(original)
    cmyk=tmp_path/'cmyk.jpg';Image.new('CMYK',(4,3)).save(cmyk)
    profile=tmp_path/'profile.png';Image.new('RGB',(4,3)).save(profile,icc_profile=b'invalid')
    result=invoke(work,'render',cmyk,profile,'--width',512,'--height',512,success=3)
    assert 'untagged_cmyk' in result.stdout and 'invalid_profile' in result.stdout
