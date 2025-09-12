use picto_py::services::get_server_path;
use tauri::test::{mock_app, MockBuilder};

#[tokio::test]
async fn test_get_server_path() {
    let app = MockBuilder::new().build().unwrap();
    let handle = app.handle().clone();
    
    let result = get_server_path(handle);
    assert!(result.is_ok(), "get_server_path should return Ok");
    
    let path = result.unwrap();
    assert!(path.contains("resources/backend"), "Path should contain resources/backend");
}