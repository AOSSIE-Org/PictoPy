use tauri::{AppHandle, Runtime};

// Only the health check and the Windows shutdown path read these.
#[cfg(any(windows, feature = "bundled-sidecars"))]
pub const ENDPOINTS: [(&str, &str, &str); 2] = [
    (
        "BACKEND",
        "http://localhost:52123/shutdown",
        "http://localhost:52123/health",
    ),
    (
        "SYNC",
        "http://localhost:52124/shutdown",
        "http://localhost:52124/health",
    ),
];

#[cfg(feature = "bundled-sidecars")]
fn is_process_alive() -> bool {
    use reqwest::blocking::Client;

    let client = match Client::builder().build() {
        Ok(c) => c,
        Err(_) => return false,
    };

    for (name, _, health) in &ENDPOINTS {
        match client.get(*health).send() {
            Ok(resp) if resp.status().is_success() => {
                println!("[{}] Health check OK", name)
            }
            _ => {
                return false;
            }
        }
    }
    true
}

#[cfg(feature = "bundled-sidecars")]
pub fn prod<R: Runtime>(app: &AppHandle<R>, resource_path: &std::path::Path) -> Result<(), String> {
    println!("`bundled-sidecars` feature enabled");
    let backend_path = resource_path.join("backend");
    let backend_executable = backend_path.join("PictoPy_Server");

    let sync_path = resource_path.join("sync-microservice");
    let sync_executable = sync_path.join("PictoPy_Sync");

    if is_process_alive() {
        return Ok(());
    }

    let (mut backend_rx, backend_child) = app
        .shell()
        .command(&backend_executable)
        .current_dir(&backend_path)
        .spawn()
        .map_err(|e| format!("Failed to spawn backend: {:?}", e))?;

    println!("Backend spawned with PID {}", backend_child.pid());

    let (mut sync_rx, sync_child) = app
        .shell()
        .command(&sync_executable)
        .current_dir(&sync_path)
        .spawn()
        .map_err(|e| format!("Failed to spawn sync: {:?}", e))?;

    println!("Sync spawned with PID {}", sync_child.pid());

    use tauri_plugin_shell::process::CommandEvent;
    use tauri_plugin_shell::ShellExt;
    tauri::async_runtime::spawn(async move {
        while let Some(event) = backend_rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    println!("[SERVER STDOUT] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Stderr(line) => {
                    println!("[SERVER STDERR] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Error(err) => {
                    println!("[SERVER ERROR] {}", err);
                }
                CommandEvent::Terminated(payload) => {
                    println!(
                        "[SERVER EXIT] code={:?}, signal={:?}",
                        payload.code, payload.signal
                    );
                }
                _ => {}
            }
        }
    });

    tauri::async_runtime::spawn(async move {
        while let Some(event) = sync_rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    println!("[SYNC STDOUT] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Stderr(line) => {
                    println!("[SYNC STDERR] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Error(err) => {
                    println!("[SYNC ERROR] {}", err);
                }
                CommandEvent::Terminated(payload) => {
                    println!(
                        "[SYNC EXIT] code={:?}, signal={:?}",
                        payload.code, payload.signal
                    );
                }
                _ => {}
            }
        }
    });

    Ok(())
}

#[cfg(not(feature = "bundled-sidecars"))]
pub fn prod<R: Runtime>(
    _app: &AppHandle<R>,
    _resource_path: &std::path::Path,
) -> Result<(), String> {
    prod_without_bundled_sidecars()
}

#[cfg(not(feature = "bundled-sidecars"))]
fn prod_without_bundled_sidecars() -> Result<(), String> {
    // `cargo tauri dev` intentionally omits this feature; the backend/sync
    // services are run separately during local development.
    if cfg!(debug_assertions) {
        return Ok(());
    }

    // A release build without this feature would otherwise launch with no
    // backend and no indication anything is wrong (see issue #1347).
    Err(
        "Release build is missing the `bundled-sidecars` feature: the bundled \
        backend/sync services will never be started. Rebuild with \
        `--features bundled-sidecars`."
            .to_string(),
    )
}

#[cfg(all(test, not(feature = "bundled-sidecars")))]
mod tests {
    use super::*;

    #[test]
    fn no_op_in_debug_builds_fails_loudly_in_release_builds() {
        // Goes through prod() itself, the function setup calls, not just the helper.
        let app = tauri::test::mock_app();
        let result = prod(app.handle(), std::path::Path::new("resources"));

        if cfg!(debug_assertions) {
            assert_eq!(result, Ok(()));
        } else {
            assert!(result.is_err());
        }
    }
}
