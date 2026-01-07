// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod services;

use std::sync::Mutex;
use sysinfo::{Pid, Signal, System};
use tauri::path::BaseDirectory;
use tauri::{Manager, Window, WindowEvent};
use tauri_plugin_shell::process::CommandEvent;
use tauri_plugin_shell::ShellExt;

#[derive(Default)]
struct Pids {
    backend: u32,
    sync: u32,
}

fn on_window_event(window: &Window, event: &WindowEvent) {
    if !matches!(event, WindowEvent::CloseRequested { .. }) {
        return;
    }

    let app_handle = window.app_handle();
    let state = app_handle.state::<Mutex<Pids>>();

    let state = state.lock().unwrap();

    if state.backend != 0 {
        let _ = kill_process_tree(state.backend);
    }

    if state.sync != 0 {
        let _ = kill_process_tree(state.sync);
    }

    drop(state);
    app_handle.exit(0);
}

#[cfg(unix)]
fn kill_process(process: &sysinfo::Process) {
    use sysinfo::Signal;
    let _ = process.kill_with(Signal::Term);
}

#[cfg(windows)]
fn kill_process(process: &sysinfo::Process) {
    let _ = process.kill();
}
fn kill_process_tree(pid: u32) -> Result<(), String> {
    let mut system = System::new_all();
    system.refresh_all();

    let root_pid = Pid::from_u32(pid);
    let mut to_kill = Vec::new();

    fn collect_children(system: &System, parent: Pid, out: &mut Vec<Pid>) {
        for (pid, process) in system.processes() {
            if process.parent() == Some(parent) {
                collect_children(system, *pid, out);
                out.push(*pid);
            }
        }
    }

    collect_children(&system, root_pid, &mut to_kill);
    to_kill.push(root_pid);

    for pid in to_kill {
        if let Some(process) = system.process(pid) {
            kill_process(process);
        }
    }

    Ok(())
}
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(Mutex::new(Pids::default()))
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            let resource_path = app.path().resolve("resources", BaseDirectory::Resource)?;
            println!("Resource path: {:?}", resource_path);

            let backend_path = resource_path.join("backend");
            let backend_executable = backend_path.join("PictoPy_Server");

            let sync_path = resource_path.join("sync-microservice");
            let sync_executable = sync_path.join("PictoPy_Sync");

            let (mut backend_rx, backend_child) = app
                .shell()
                .command(&backend_executable)
                .current_dir(backend_path)
                .spawn()
                .map_err(|e| format!("Failed to Spawn {:?}: {:?}", &backend_executable, e))?;

            tauri::async_runtime::spawn(async move {
                while let Some(event) = backend_rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            println!("[SERVER STDOUT] {:?}", String::from_utf8(line));
                        }
                        CommandEvent::Stderr(line) => {
                            println!("[SERVER STDERR] {:?}", String::from_utf8(line));
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

            let (mut sync_rx, sync_child) = app
                .shell()
                .command(&sync_executable)
                .current_dir(sync_path)
                .spawn()
                .map_err(|e| format!("Failed to Spawn {:?}: {:?}", &sync_executable, e))?;
            sync_child.pid();

            tauri::async_runtime::spawn(async move {
                while let Some(event) = sync_rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            println!("[SYNC STDOUT] {:?}", String::from_utf8(line));
                        }
                        CommandEvent::Stderr(line) => {
                            println!("[SYNC STDERR] {:?}", String::from_utf8(line));
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

            let state = app.state::<Mutex<Pids>>();
            {
                let mut pids = state.lock().unwrap();
                pids.backend = backend_child.pid();
                pids.sync = sync_child.pid();
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            services::get_resources_folder_path,
        ])
        .on_window_event(on_window_event)
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
