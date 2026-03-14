import pytest
from unittest.mock import patch, MagicMock
from app.utils.ONNX import create_inference_session_with_fallback

def test_create_inference_session_success():
    with patch('app.utils.ONNX.onnxruntime.InferenceSession') as mock_session, \
         patch('app.utils.ONNX.ONNX_util_get_execution_providers', return_value=['CUDAExecutionProvider']):
        
        mock_logger = MagicMock()
        session = create_inference_session_with_fallback('dummy_path', mock_logger)
        
        mock_session.assert_called_once_with('dummy_path', providers=['CUDAExecutionProvider'])
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()
        assert session == mock_session.return_value

def test_create_inference_session_fallback_success():
    with patch('app.utils.ONNX.onnxruntime.InferenceSession') as mock_session, \
         patch('app.utils.ONNX.ONNX_util_get_execution_providers', return_value=['CUDAExecutionProvider']):
        
        # Make the first call raise an exception, and the second call succeed
        cpu_success_mock = MagicMock()
        mock_session.side_effect = [Exception("CUDA failed"), cpu_success_mock]
        
        mock_logger = MagicMock()
        session = create_inference_session_with_fallback('dummy_path', mock_logger)
        
        assert mock_session.call_count == 2
        mock_session.assert_any_call('dummy_path', providers=['CUDAExecutionProvider'])
        mock_session.assert_any_call('dummy_path', providers=['CPUExecutionProvider'])
        
        mock_logger.warning.assert_called_once()
        assert "CUDA failed" in mock_logger.warning.call_args[0][0]
        mock_logger.error.assert_not_called()
        
        # Second value in side_effect is the success mock
        # Verify the returned session is the successful CPU fallback mock
        assert session == cpu_success_mock

def test_create_inference_session_fallback_failure():
    with patch('app.utils.ONNX.onnxruntime.InferenceSession') as mock_session, \
         patch('app.utils.ONNX.ONNX_util_get_execution_providers', return_value=['CUDAExecutionProvider']):
        
        # Make both calls raise an exception
        mock_session.side_effect = [Exception("CUDA failed"), Exception("CPU failed")]
        
        mock_logger = MagicMock()
        
        with pytest.raises(Exception, match="CPU failed"):
            create_inference_session_with_fallback('dummy_path', mock_logger, model_name="TestModel")
            
        assert mock_session.call_count == 2
        mock_logger.warning.assert_called_once()
        mock_logger.error.assert_called_once()
        assert "TestModel" in mock_logger.error.call_args[0][0]
        assert "CPU failed" in mock_logger.error.call_args[0][0]

