import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_comparison
from static_renderers import bilinear, glass_maps, rectangle, reflect_axis


def test_bilinear_preserves_corners_and_averages_center():
    pixels = np.array([[[0, 0, 0], [4, 4, 4]], [[8, 8, 8], [12, 12, 12]]], dtype=np.float32)
    coordinates = np.array([[[0, 0], [.5, .5], [1, 1]]], dtype=np.float32)
    assert np.array_equal(bilinear(pixels, coordinates), [[[0, 0, 0], [6, 6, 6], [12, 12, 12]]])


def test_reflection_excludes_duplicate_boundary():
    assert np.array_equal(reflect_axis(np.arange(-3, 6), 3), [1, 2, 1, 0, 1, 2, 1, 0, 1])


def test_glass_map_stays_bounded_and_has_visible_displacement():
    photo = Image.new('RGB', (729, 972))
    maps = glass_maps(photo, 'strong-edge')
    yy, xx = np.mgrid[:1080, :1920]
    coordinates = maps['coordinates']
    assert np.max(np.abs(coordinates[..., 0]-xx)) <= 12.001
    assert np.max(np.abs(coordinates[..., 1]-yy)) <= 12.001
    assert maps['mask'][540, 560] == 0
    assert maps['mask'][540, 570] == 1
    assert coordinates[540, 570, 0] < 570


def test_foreground_is_restored_exactly_and_wrong_size_fails():
    photo = Image.fromarray(np.arange(9*12*3, dtype=np.uint8).reshape(12,9,3))
    frame = run_comparison.checked_frame(Image.new('RGB',(1920,1080),'red'),photo)
    x,y,w,h = rectangle(photo)
    assert frame.crop((x,y,x+w,y+h)).tobytes() == photo.tobytes()
    assert frame.getpixel((0,0)) == (255,0,0)
    with pytest.raises(ValueError):
        run_comparison.checked_frame(Image.new('RGB',(100,100)),photo)


def test_process_memory_guard_stops_an_actual_child(tmp_path, monkeypatch):
    photo = tmp_path/'photo.png'
    Image.new('RGB',(4,3)).save(photo)
    spec = {'case_id':'test','input_id':'test','tool':'S1','method':'solid','preset':'default',
            'prepared':str(photo),'work':str(tmp_path),'output':str(tmp_path/'out.png'),
            'thumbnail':str(tmp_path/'thumb.png')}
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    monkeypatch.setattr(run_comparison,'MEMORY_LIMIT',1)
    result=run_comparison.supervise(path)
    assert result['status']=='failed'
    assert 'memory exceeded' in result['error']
    assert not (tmp_path/'out.png').exists()


def test_report_resolves_positive_rating_without_mutation(tmp_path):
    from comparison_report import resolve_rated_image, write_report
    old = tmp_path / 'case.png'
    rated = tmp_path / 'casea.png'
    rated.write_bytes(b'unchanged')
    row = {'image': str(old)}
    write_report({}, [row], tmp_path / 'index.html', tmp_path)
    assert resolve_rated_image(old) == rated
    assert row == {'image': str(old)}
    assert 'casea.png' in (tmp_path / 'index.html').read_text()
    assert rated.read_bytes() == b'unchanged'
