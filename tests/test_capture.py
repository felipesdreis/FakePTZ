from unittest.mock import MagicMock, patch

import cv2
import pytest

from fakeptz.video import CaptureError, open_capture


def _mock_capture(opened=True, width=1920, height=1080, fps=30):
    mock = MagicMock()
    mock.isOpened.return_value = opened
    values = {
        cv2.CAP_PROP_FRAME_WIDTH: width,
        cv2.CAP_PROP_FRAME_HEIGHT: height,
        cv2.CAP_PROP_FPS: fps,
    }
    mock.get.side_effect = lambda prop: values.get(prop, 0)
    return mock


@patch("fakeptz.video.cv2.VideoCapture")
def test_open_capture_success(mock_video_capture):
    mock_video_capture.return_value = _mock_capture()

    capture = open_capture(0, 1920, 1080, 30)

    assert capture is mock_video_capture.return_value


@patch("fakeptz.video.cv2.VideoCapture")
def test_open_capture_device_not_opened(mock_video_capture):
    mock_video_capture.return_value = _mock_capture(opened=False)

    with pytest.raises(CaptureError):
        open_capture(0, 1920, 1080, 30)


@patch("fakeptz.video.cv2.VideoCapture")
def test_open_capture_unsupported_resolution(mock_video_capture):
    mock_video_capture.return_value = _mock_capture(width=1280, height=720)

    with pytest.raises(CaptureError):
        open_capture(0, 1920, 1080, 30)


@patch("fakeptz.video.cv2.VideoCapture")
def test_open_capture_unsupported_fps(mock_video_capture):
    mock_video_capture.return_value = _mock_capture(fps=15)

    with pytest.raises(CaptureError):
        open_capture(0, 1920, 1080, 30)
