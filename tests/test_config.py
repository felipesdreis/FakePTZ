from fakeptz.config import CropMode, CROP_COORDS


def test_crop_coords_match_spec():
    assert CROP_COORDS[CropMode.ESQUERDA] == (180, 900, 0, 1280)
    assert CROP_COORDS[CropMode.CENTRO] == (180, 900, 320, 1600)
    assert CROP_COORDS[CropMode.DIREITA] == (180, 900, 640, 1920)
