// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod services;

use sysinfo::System;
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::path::BaseDirectory;
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{Manager, Window, WindowEvent};
use tauri_plugin_autostart::ManagerExt;
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

// Hide the window instead of exiting so the app lives in the system tray.
// The user can quit via the tray context menu's "Quit" item.
fn on_window_event(window: &Window, event: &WindowEvent) {
    if let WindowEvent::CloseRequested { api, .. } = event {
        api.prevent_close();
        let _ = window.hide();
    }
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

#[tauri::command]
fn enable_autostart(app: tauri::AppHandle) -> Result<(), String> {
    app.autolaunch().enable().map_err(|e| e.to_string())
}

#[tauri::command]
fn disable_autostart(app: tauri::AppHandle) -> Result<(), String> {
    app.autolaunch().disable().map_err(|e| e.to_string())
}

#[tauri::command]
fn is_autostart_enabled(app: tauri::AppHandle) -> Result<bool, String> {
    app.autolaunch().is_enabled().map_err(|e| e.to_string())
}

fn main() {
    tauri::Builder::default()
        // Auto-start: pass --minimized so the window starts hidden when launched at boot
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            Some(vec!["--minimized"]),
        ))
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

            // When auto-started at boot (--minimized flag), keep the window hidden
            if std::env::args().any(|a| a == "--minimized") {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.hide();
                }
            }

            // System tray: context menu with Show / Quit
            let show_item = MenuItem::with_id(app, "show", "Show", true, None::<&str>)?;
            let separator = PredefinedMenuItem::separator(app)?;
            let quit_item = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_item, &separator, &quit_item])?;

            TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("PictoPy")
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                    }
                    "quit" => {
                        let _ = kill_process_tree();
                        app.exit(0);
                    }
                    _ => {}
                })
                // Left-click on the tray icon also shows the window
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            services::get_resources_folder_path,
            enable_autostart,
            disable_autostart,
            is_autostart_enabled,
        ])
        .on_window_event(on_window_event)
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
