import asyncio
from unittest.mock import MagicMock, patch

import numpy as np

from fakeptz.video import CaptureError, VideoPipeline


def _mock_capture_with_frames(frame_count, frame_shape=(1080, 1920, 3)):
    capture = MagicMock()
    frame = np.zeros(frame_shape, dtype=np.uint8)
    capture.read.side_effect = [(True, frame)] * frame_count + [(False, None)]
    return capture


@patch("fakeptz.video.pyvirtualcam.Camera")
@patch("fakeptz.video.open_capture")
def test_run_processes_frames_until_read_fails(mock_open_capture, mock_camera_cls):
    capture = _mock_capture_with_frames(3)
    mock_open_capture.return_value = capture
    camera_instance = mock_camera_cls.return_value

    pipeline = VideoPipeline()
    errors = []

    asyncio.run(pipeline.run(on_error=errors.append))

    assert camera_instance.send.call_count == 3
    assert pipeline.status == "ERRO"
    assert errors == ["Falha ao ler frame do dispositivo de captura."]
    capture.release.assert_called_once()


@patch("fakeptz.video.open_capture")
def test_run_reports_capture_error(mock_open_capture):
    mock_open_capture.side_effect = CaptureError("Não foi possível abrir o dispositivo de captura 0.")

    pipeline = VideoPipeline()
    errors = []

    asyncio.run(pipeline.run(on_error=errors.append))

    assert pipeline.status == "ERRO"
    assert errors == ["Não foi possível abrir o dispositivo de captura 0."]


@patch("fakeptz.video.pyvirtualcam.Camera")
@patch("fakeptz.video.open_capture")
def test_run_processes_720p_frames(mock_open_capture, mock_camera_cls):
    capture = _mock_capture_with_frames(2, frame_shape=(720, 1280, 3))
    mock_open_capture.return_value = capture
    camera_instance = mock_camera_cls.return_value

    pipeline = VideoPipeline()
    errors = []

    asyncio.run(pipeline.run(on_error=errors.append))

    assert camera_instance.send.call_count == 2
    sent_frame = camera_instance.send.call_args_list[0][0][0]
    assert sent_frame.shape == (720, 1280, 3)


@patch("fakeptz.video.pyvirtualcam.Camera")
@patch("fakeptz.video.open_capture")
def test_run_reports_virtual_camera_error(mock_open_capture, mock_camera_cls):
    mock_open_capture.return_value = _mock_capture_with_frames(0)
    mock_camera_cls.side_effect = RuntimeError("driver not found")

    pipeline = VideoPipeline()
    errors = []

    asyncio.run(pipeline.run(on_error=errors.append))

    assert pipeline.status == "ERRO"
    assert errors == ["Câmera virtual indisponível: driver not found"]
