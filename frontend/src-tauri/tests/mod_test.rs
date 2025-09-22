use picto_py::services::file_service::get_server_path;

#[test]
fn test_get_server_path() {
    let result = get_server_path();
    assert!(result.is_some());
}
