from unittest.mock import MagicMock, patch

from app.utils.ONNX import ONNX_util_get_execution_providers
from app.models.SigLIP2Text import SigLIP2Text

MACOS_PROVIDERS = ["CoreMLExecutionProvider", "CPUExecutionProvider"]


def _metadata(gpu: bool) -> dict:
    return {"user_preferences": {"GPU_Acceleration": gpu}}


class TestExecutionProviderExclusion:
    @patch("onnxruntime.get_available_providers", return_value=MACOS_PROVIDERS)
    @patch("app.database.metadata.db_get_metadata", return_value=_metadata(True))
    def test_exclude_filters_provider(self, mock_meta, mock_providers):
        result = ONNX_util_get_execution_providers(exclude=("CoreMLExecutionProvider",))
        assert result == ["CPUExecutionProvider"]

    @patch("onnxruntime.get_available_providers", return_value=MACOS_PROVIDERS)
    @patch("app.database.metadata.db_get_metadata", return_value=_metadata(True))
    def test_no_exclude_keeps_all_providers(self, mock_meta, mock_providers):
        assert ONNX_util_get_execution_providers() == MACOS_PROVIDERS

    @patch(
        "onnxruntime.get_available_providers",
        return_value=["CoreMLExecutionProvider"],
    )
    @patch("app.database.metadata.db_get_metadata", return_value=_metadata(True))
    def test_excluding_everything_falls_back_to_cpu(self, mock_meta, mock_providers):
        result = ONNX_util_get_execution_providers(exclude=("CoreMLExecutionProvider",))
        assert result == ["CPUExecutionProvider"]

    @patch("app.database.metadata.db_get_metadata", return_value=_metadata(False))
    def test_gpu_off_ignores_exclude(self, mock_meta):
        result = ONNX_util_get_execution_providers(exclude=("CoreMLExecutionProvider",))
        assert result == ["CPUExecutionProvider"]


class TestSigLIP2SessionExcludesCoreML:
    @patch("onnxruntime.get_available_providers", return_value=MACOS_PROVIDERS)
    @patch("app.database.metadata.db_get_metadata", return_value=_metadata(True))
    @patch("onnxruntime.InferenceSession")
    @patch("os.path.exists", return_value=True)
    def test_session_created_without_coreml(
        self, mock_exists, mock_session_cls, mock_meta, mock_providers
    ):
        """Regression test for macOS: CoreML cannot run the full SigLIP2
        graph, so ONNXSessionBase must never hand it to InferenceSession."""
        fake = MagicMock()
        tensor = MagicMock()
        tensor.name = "input_ids"
        tensor2 = MagicMock()
        tensor2.name = "attention_mask"
        fake.get_inputs.return_value = [tensor, tensor2]
        fake.get_outputs.return_value = [MagicMock()]
        mock_session_cls.return_value = fake

        model = SigLIP2Text("app/models/ONNX_Exports/SigLIP2_Base_Text.onnx")
        try:
            model.get_session()
        finally:
            model.close()

        providers = mock_session_cls.call_args.kwargs["providers"]
        assert "CoreMLExecutionProvider" not in providers
        assert providers == ["CPUExecutionProvider"]
