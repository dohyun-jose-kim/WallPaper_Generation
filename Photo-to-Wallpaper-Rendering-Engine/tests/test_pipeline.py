import io
import sys
from pathlib import Path
import pytest
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wallpaper_engine.image_preparation import prepare_pixels, clean_png_bytes
from wallpaper_engine.settings import validate_target, inspect_source, fit_box, WARNING
from wallpaper_engine.worker import request


def encoded(image, **options):
    stream = io.BytesIO()
    image.save(stream, format='PNG', **options)
    return stream.getvalue()


@pytest.mark.parametrize('size,warn', [((512,1024),False),((1024,512),False),((512,1536),True),((1536,512),True),((3440,1440),True),((512,512),False)])
def test_ratio_boundaries(size,warn):
    assert bool(validate_target(*size)) == warn


@pytest.mark.parametrize('size', [(511,512),(8193,512),(8192,8192),(512,1537),(1537,512)])
def test_size_limits(size):
    with pytest.raises(ValueError): validate_target(*size)


@pytest.mark.parametrize('border', [.03,.05,.20])
@pytest.mark.parametrize('canvas', [(1920,1080),(1080,1920),(512,512),(1536,512)])
def test_geometry(canvas,border):
    photo, details=prepare_pixels(encoded(Image.new('RGB',(31,23))),fit_box(*canvas,border),canvas)
    x,y,xx,yy=details['protected_rectangle_xyxy_exclusive']
    assert 0<=x<xx<=canvas[0] and 0<=y<yy<=canvas[1]
    assert photo.width<=fit_box(*canvas,border)[0]
    assert abs(photo.width/photo.height - 31/23)<.02


def test_grayscale_alpha_palette_and_orientation():
    gray,_=prepare_pixels(encoded(Image.new('L',(3,2),80)),(3,2))
    assert gray.getpixel((0,0))==(80,80,80)
    alpha,_=prepare_pixels(encoded(Image.new('RGBA',(3,2),(255,0,0,0))),(3,2))
    assert alpha.getpixel((0,0))==(22,24,29)
    exif=Image.Exif();exif[274]=6
    assert inspect_source(encoded(Image.new('RGB',(3,2)),exif=exif))==(2,3)
    pal=Image.new('P',(3,2));pal.info['transparency']=0
    assert prepare_pixels(encoded(pal),(3,2))[0].getpixel((0,0))==(22,24,29)


def test_animation_and_other_formats_rejected():
    image=Image.new('RGB',(4,3)); stream=io.BytesIO()
    image.save(stream,format='PNG',save_all=True,append_images=[Image.new('RGB',(4,3),'red')],duration=100)
    with pytest.raises(ValueError): prepare_pixels(stream.getvalue())
    stream=io.BytesIO();image.save(stream,format='GIF')
    with pytest.raises(ValueError): inspect_source(stream.getvalue())


def test_protocol_rejects_unknown_versions():
    for line in ['{}','{"version":2,"type":"job"}','[]']:
        with pytest.raises(ValueError): request(line)
