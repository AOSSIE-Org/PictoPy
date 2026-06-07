// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod services;

use sysinfo::System;
use tauri::path::BaseDirectory;
use tauri::{Manager, Window, WindowEvent};
use tauri_plugin_shell::ShellExt;

const ENDPOINTS: [(&str, &str, &str); 2] = [
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

#[cfg(feature = "ci")]
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

fn on_window_event(window: &Window, event: &WindowEvent) {
    if !matches!(event, WindowEvent::CloseRequested { .. }) {
        return;
    }

    let _ = kill_process_tree();
    window.app_handle().exit(0);
}

#[cfg(unix)]
fn kill_process(process: &sysinfo::Process) {
    use sysinfo::Signal;
    let _ = process.kill_with(Signal::Term);
}

#[cfg(windows)]
pub fn kill_process(_process: &sysinfo::Process) -> Result<(), String> {
    use reqwest::blocking::Client;

    let client = Client::builder().build().map_err(|e| e.to_string())?;

    for (name, url, _) in &ENDPOINTS {
        match client.post(*url).send() {
            Ok(resp) => {
                let status = resp.status();

                if status.is_success() {
                    println!("[{}] Shutdown OK ({})", name, status);
                }
            }
            Err(_err) => {}
        }
    }

    Ok(())
}

fn kill_process_tree() -> Result<(), String> {
    let mut system = System::new_all();
    system.refresh_all();

    let target_names = [
        "PictoPy_Server",
        "PictoPy_Sync",
        "PictoPy_Server.exe",
        "PictoPy_Sync.exe",
    ];

    for process in system.processes().values() {
        let name = process.name().to_string_lossy();

        if target_names.iter().any(|t| name.eq_ignore_ascii_case(t)) {
            let _ = kill_process(process);
        }
    }

    Ok(())
}

#[cfg(feature = "ci")]
fn prod(app: &tauri::AppHandle, resource_path: &std::path::Path) -> Result<(), String> {
    println!("`ci` feature enabled");
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

#[cfg(not(feature = "ci"))]
fn prod(_app: &tauri::AppHandle, _resource_path: &std::path::Path) -> Result<(), String> {
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .plugin(
            tauri_plugin_log::Builder::new()
                .level(log::LevelFilter::Info)
                .max_file_size(5_000_000) // 5 MB per log file
                .rotation_strategy(tauri_plugin_log::RotationStrategy::KeepAll)
                .build(),
        )
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            let resource_path = app.path().resolve("resources", BaseDirectory::Resource)?;
            println!("Resource path: {:?}", resource_path);

            prod(app.handle(), &resource_path)?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            services::get_resources_folder_path,
        ])
        .on_window_event(on_window_event)
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
