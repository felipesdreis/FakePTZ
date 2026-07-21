from fakeptz.config import MODE_PAN_TILT, CropMode, CROP_COORDS, crop_coords_for


def test_crop_coords_match_spec():
    assert CROP_COORDS[CropMode.ESQUERDA] == (180, 900, 0, 1280)
    assert CROP_COORDS[CropMode.CENTRO] == (180, 900, 320, 1600)
    assert CROP_COORDS[CropMode.DIREITA] == (180, 900, 640, 1920)


def test_crop_coords_for_1920x1080_matches_legacy_table():
    esquerda_pan, esquerda_tilt = MODE_PAN_TILT[CropMode.ESQUERDA]
    centro_pan, centro_tilt = MODE_PAN_TILT[CropMode.CENTRO]
    direita_pan, direita_tilt = MODE_PAN_TILT[CropMode.DIREITA]

    assert crop_coords_for(1920, 1080, pan=esquerda_pan, tilt=esquerda_tilt) == (180, 900, 0, 1280)
    assert crop_coords_for(1920, 1080, pan=centro_pan, tilt=centro_tilt) == (180, 900, 320, 1600)
    assert crop_coords_for(1920, 1080, pan=direita_pan, tilt=direita_tilt) == (180, 900, 640, 1920)


def test_crop_coords_for_1280x720():
    assert crop_coords_for(1280, 720, pan=0.0, tilt=0.5) == (120, 600, 0, 853)
    assert crop_coords_for(1280, 720, pan=0.5, tilt=0.5) == (120, 600, 214, 1067)
    assert crop_coords_for(1280, 720, pan=1.0, tilt=0.5) == (120, 600, 427, 1280)


def test_crop_coords_for_default_is_full_center_no_zoom():
    assert crop_coords_for(1920, 1080) == (180, 900, 320, 1600)


def test_crop_coords_for_zoom_shrinks_crop_symmetrically():
    h_start, h_end, w_start, w_end = crop_coords_for(1920, 1080, zoom=2.0, pan=0.5, tilt=0.5)
    assert (w_end - w_start) == 640
    assert (h_end - h_start) == 360


def test_crop_coords_for_zoom_clamps_to_configured_range():
    assert crop_coords_for(1920, 1080, zoom=0.1) == crop_coords_for(1920, 1080, zoom=1.0)
    assert crop_coords_for(1920, 1080, zoom=10.0) == crop_coords_for(1920, 1080, zoom=3.0)


def test_crop_coords_for_pan_clamps_to_valid_range():
    assert crop_coords_for(1920, 1080, pan=-1.0) == crop_coords_for(1920, 1080, pan=0.0)
    assert crop_coords_for(1920, 1080, pan=2.0) == crop_coords_for(1920, 1080, pan=1.0)


def test_crop_coords_for_tilt_clamps_to_valid_range():
    assert crop_coords_for(1920, 1080, tilt=-1.0) == crop_coords_for(1920, 1080, tilt=0.0)
    assert crop_coords_for(1920, 1080, tilt=2.0) == crop_coords_for(1920, 1080, tilt=1.0)
