import importlib
from unittest.mock import MagicMock, patch

import onnxruntime
import pytest

from app.config import settings
from app.models.FaceNet import FaceNet
from app.models.SigLIP2Text import SigLIP2Text
from app.models.YOLO import YOLO
from app.utils.ONNX import ONNX_util_get_session_options


class _FakeTensor:
    def __init__(self, name: str, shape: list[int] | None = None):
        self.name = name
        self.shape = shape or [1, 3, 640, 640]


def _mock_ort_session() -> MagicMock:
    session = MagicMock()
    session.get_inputs.return_value = [
        _FakeTensor("input_ids"),
        _FakeTensor("attention_mask"),
    ]
    session.get_outputs.return_value = [_FakeTensor("output")]
    return session


class TestONNXSessionOptionsHelper:
    def test_default_session_options(self):
        """Verify default configuration: single intra-op thread, sequential execution, fixed inter-op=1."""
        opts = ONNX_util_get_session_options()
        assert isinstance(opts, onnxruntime.SessionOptions)
        assert opts.intra_op_num_threads == 1
        assert opts.inter_op_num_threads == 1
        assert opts.execution_mode == onnxruntime.ExecutionMode.ORT_SEQUENTIAL

    def test_explicit_thread_overrides(self):
        """Verify explicit keyword argument overrides for intra-op thread count."""
        opts = ONNX_util_get_session_options(intra_op_num_threads=4)
        assert opts.intra_op_num_threads == 4
        assert opts.inter_op_num_threads == 1
        assert opts.execution_mode == onnxruntime.ExecutionMode.ORT_SEQUENTIAL

    def test_env_var_overrides(self, monkeypatch):
        """Verify environment variable overrides update defaults."""
        monkeypatch.setenv("ONNX_INTRA_OP_NUM_THREADS", "4")
        importlib.reload(settings)
        try:
            opts = ONNX_util_get_session_options()
            assert opts.intra_op_num_threads == 4
            assert opts.inter_op_num_threads == 1
        finally:
            monkeypatch.delenv("ONNX_INTRA_OP_NUM_THREADS", raising=False)
            importlib.reload(settings)

    def test_invalid_env_var_fallback(self, monkeypatch):
        """Verify invalid environment variables fall back to default of 1."""
        # Non-integer string
        monkeypatch.setenv("ONNX_INTRA_OP_NUM_THREADS", "invalid")
        importlib.reload(settings)
        try:
            opts = ONNX_util_get_session_options()
            assert opts.intra_op_num_threads == 1
            assert opts.inter_op_num_threads == 1
        finally:
            monkeypatch.delenv("ONNX_INTRA_OP_NUM_THREADS", raising=False)
            importlib.reload(settings)

        # Zero and negative values (min_value=1)
        monkeypatch.setenv("ONNX_INTRA_OP_NUM_THREADS", "0")
        importlib.reload(settings)
        try:
            opts = ONNX_util_get_session_options()
            assert opts.intra_op_num_threads == 1
            assert opts.inter_op_num_threads == 1
        finally:
            monkeypatch.delenv("ONNX_INTRA_OP_NUM_THREADS", raising=False)
            importlib.reload(settings)

        monkeypatch.setenv("ONNX_INTRA_OP_NUM_THREADS", "-5")
        importlib.reload(settings)
        try:
            opts = ONNX_util_get_session_options()
            assert opts.intra_op_num_threads == 1
            assert opts.inter_op_num_threads == 1
        finally:
            monkeypatch.delenv("ONNX_INTRA_OP_NUM_THREADS", raising=False)
            importlib.reload(settings)

    def test_invalid_explicit_arguments_raise_value_error(self):
        """Verify explicit arguments < 1 raise ValueError."""
        with pytest.raises(ValueError, match="intra_op_num_threads must be >= 1"):
            ONNX_util_get_session_options(intra_op_num_threads=0)

        with pytest.raises(ValueError, match="intra_op_num_threads must be >= 1"):
            ONNX_util_get_session_options(intra_op_num_threads=-2)


class TestONNXConstructorsPassSessionOptions:
    @patch("onnxruntime.InferenceSession")
    @patch("os.path.exists", return_value=True)
    def test_onnx_session_base_passes_session_options(
        self, mock_exists, mock_session_cls
    ):
        """Verify ONNXSessionBase._create_session passes sess_options to InferenceSession."""
        mock_session_cls.return_value = _mock_ort_session()
        model = SigLIP2Text("app/models/ONNX_Exports/SigLIP2_Base_Text.onnx")
        try:
            model.get_session()
        finally:
            model.close()

        assert "sess_options" in mock_session_cls.call_args.kwargs
        sess_options = mock_session_cls.call_args.kwargs["sess_options"]
        assert isinstance(sess_options, onnxruntime.SessionOptions)
        assert sess_options.intra_op_num_threads == 1
        assert sess_options.inter_op_num_threads == 1
        assert sess_options.execution_mode == onnxruntime.ExecutionMode.ORT_SEQUENTIAL

    @patch("onnxruntime.InferenceSession")
    @patch("os.path.exists", return_value=True)
    def test_facenet_passes_session_options(self, mock_exists, mock_session_cls):
        """Verify FaceNet.get_session passes sess_options to InferenceSession."""
        mock_session_cls.return_value = _mock_ort_session()
        model = FaceNet("app/models/ONNX_Exports/FaceNet_128D.onnx")
        model.get_session()

        assert "sess_options" in mock_session_cls.call_args.kwargs
        sess_options = mock_session_cls.call_args.kwargs["sess_options"]
        assert isinstance(sess_options, onnxruntime.SessionOptions)
        assert sess_options.intra_op_num_threads == 1
        assert sess_options.inter_op_num_threads == 1
        assert sess_options.execution_mode == onnxruntime.ExecutionMode.ORT_SEQUENTIAL

    @patch("onnxruntime.InferenceSession")
    @patch("os.path.exists", return_value=True)
    def test_yolo_passes_session_options(self, mock_exists, mock_session_cls):
        """Verify YOLO.get_session passes sess_options to InferenceSession."""
        mock_session_cls.return_value = _mock_ort_session()
        model = YOLO("app/models/ONNX_Exports/YOLOv11_Small.onnx")
        try:
            model.get_session()
        finally:
            model.close()

        assert "sess_options" in mock_session_cls.call_args.kwargs
        sess_options = mock_session_cls.call_args.kwargs["sess_options"]
        assert isinstance(sess_options, onnxruntime.SessionOptions)
        assert sess_options.intra_op_num_threads == 1
        assert sess_options.inter_op_num_threads == 1
        assert sess_options.execution_mode == onnxruntime.ExecutionMode.ORT_SEQUENTIAL
