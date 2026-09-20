// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod services;

use sysinfo::System;
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::path::BaseDirectory;
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{Manager, Window, WindowEvent};
use tauri_plugin_autostart::ManagerExt;
use tauri_plugin_store::StoreExt;

const STORE_PATH: &str = "settings.json";
const CLOSE_TO_TRAY_KEY: &str = "close_to_tray";

fn on_window_event(window: &Window, event: &WindowEvent) {
    if let WindowEvent::CloseRequested { api, .. } = event {
        // Secondary windows (e.g. model-manager) close normally.
        if window.label() != "main" {
            return;
        }

        // Take control of the main window's close event.
        api.prevent_close();

        let app = window.app_handle().clone();
        let close_to_tray = app
            .store(STORE_PATH)
            .ok()
            .and_then(|s| s.get(CLOSE_TO_TRAY_KEY))
            .and_then(|v| v.as_bool())
            .unwrap_or(true); // default: hide to tray

        if close_to_tray {
            let _ = window.hide();
        } else {
            if let Some(manager) = app.get_webview_window("model-manager") {
                let _ = manager.close();
            }
            // Before the backend goes: an orphaned tunnel would leave an album
            // reachable from the internet.
            services::tunnel::shutdown(&app);
            let _ = kill_process_tree();
            app.exit(0);
        }
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

    for (name, url, _) in &services::sidecars::ENDPOINTS {
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

#[tauri::command]
async fn open_model_manager(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("model-manager") {
        let _ = window.show();
        let _ = window.set_focus();
        return Ok(());
    }

    tauri::WebviewWindowBuilder::new(
        &app,
        "model-manager",
        tauri::WebviewUrl::App("index.html?route=/model-manager".into()),
    )
    .title("Settings - Model Manager")
    .inner_size(1023.0, 632.0)
    .min_inner_size(1023.0, 632.0)
    .build()
    .map_err(|e| e.to_string())?;

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

#[tauri::command]
fn get_close_to_tray(app: tauri::AppHandle) -> Result<bool, String> {
    let store = app.store(STORE_PATH).map_err(|e| e.to_string())?;
    Ok(store
        .get(CLOSE_TO_TRAY_KEY)
        .and_then(|v| v.as_bool())
        .unwrap_or(true))
}

#[tauri::command]
fn set_close_to_tray(app: tauri::AppHandle, enabled: bool) -> Result<(), String> {
    let store = app.store(STORE_PATH).map_err(|e| e.to_string())?;
    store.set(CLOSE_TO_TRAY_KEY, enabled);
    store.save().map_err(|e| e.to_string())
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
        .manage(services::tunnel::TunnelState::new())
        .setup(|app| {
            let resource_path = app.path().resolve("resources", BaseDirectory::Resource)?;
            println!("Resource path: {:?}", resource_path);

            services::sidecars::prod(app.handle(), &resource_path)?;

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
                .icon(
                    app.default_window_icon()
                        .ok_or("no default window icon")?
                        .clone(),
                )
                .tooltip("PictoPy")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                    }
                    "quit" => {
                        services::tunnel::shutdown(app);
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
            services::tunnel::tunnel_start,
            services::tunnel::tunnel_stop,
            services::tunnel::tunnel_status,
            open_model_manager,
            enable_autostart,
            disable_autostart,
            is_autostart_enabled,
            get_close_to_tray,
            set_close_to_tray,
        ])
        .on_window_event(on_window_event)
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            // The close handler and the tray item both stop the tunnel already,
            // but neither covers every way the app can exit. This is the one
            // path all of them pass through, and an ssh child outliving
            // PictoPy would leave an album reachable from the internet.
            if let tauri::RunEvent::Exit = event {
                services::tunnel::shutdown(app);
            }
        });
}
