//! Exposing the share server beyond the LAN through an SSH reverse tunnel.
//!
//! Nothing is bundled to make this work: every desktop platform ships an ssh
//! client, and both providers below accept a plain port forward. That avoids a
//! ~40MB third-party binary in the installer, and the supply-chain question of
//! pinning one that upstream publishes from unversioned URLs.
//!
//! The child process is owned here so it dies with the app. An orphaned tunnel
//! is an album left reachable from the internet, which is a good deal worse
//! than the orphaned LAN listener the backend already guards against.

use std::path::PathBuf;
use std::sync::Mutex;
use std::time::Duration;

use tauri::{AppHandle, Manager, State};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;
use tokio::sync::mpsc::Receiver;
use tokio::time::timeout;

/// How long a provider gets to hand back a URL before we move on to the next.
const URL_TIMEOUT: Duration = Duration::from_secs(30);

#[derive(Clone, Copy)]
struct Provider {
    name: &'static str,
    /// Destination for ssh, including the user where one is expected.
    destination: &'static str,
    /// Remote port to request. localhost.run wants 80; srv.us numbers services.
    remote_port: &'static str,
    /// Host suffix identifying the assigned URL. Matched instead of the
    /// surrounding wording, because both providers print a banner containing
    /// several unrelated https links before the real one.
    url_suffix: &'static str,
}

/// Tried in order until one answers. srv.us is the intended second entry, and
/// needs a dedicated key generated first, so it lands separately rather than
/// half-built here. A fallback matters because a provider can fail while
/// looking healthy: one accepted connections and issued URLs for a tunnel it
/// then never routed anything to.
const PROVIDERS: [Provider; 1] = [Provider {
    name: "localhost.run",
    destination: "nokey@localhost.run",
    remote_port: "80",
    url_suffix: ".lhr.life",
}];

pub struct TunnelState {
    active: Mutex<Option<ActiveTunnel>>,
}

impl TunnelState {
    pub fn new() -> Self {
        Self {
            active: Mutex::new(None),
        }
    }
}

impl Default for TunnelState {
    fn default() -> Self {
        Self::new()
    }
}

struct ActiveTunnel {
    url: String,
    child: CommandChild,
}

/// The public URL in a line of provider output, if there is one.
///
/// Split on whitespace rather than pattern-matching the sentence around it: the
/// wording is the provider's to change, and one has already been observed
/// printing something different from its own documentation.
fn find_url(line: &str, suffix: &str) -> Option<String> {
    line.split_whitespace()
        .filter(|token| token.starts_with("https://"))
        .map(|token| token.trim_end_matches(['/', ',', '.']))
        .find(|token| token.ends_with(suffix))
        .map(str::to_string)
}

/// Our own known_hosts, so accepting a provider's key never edits the user's.
fn known_hosts_path(app: &AppHandle) -> Result<PathBuf, String> {
    let directory = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("no app data directory: {e}"))?
        .join("ssh");
    std::fs::create_dir_all(&directory)
        .map_err(|e| format!("could not create {}: {e}", directory.display()))?;
    Ok(directory.join("known_hosts"))
}

async fn read_url(events: &mut Receiver<CommandEvent>, suffix: &str) -> Option<String> {
    while let Some(event) = events.recv().await {
        let line = match event {
            // Providers announce the URL on stdout, but ssh's own diagnostics
            // arrive on stderr, and a failed forward is only visible there.
            CommandEvent::Stdout(bytes) | CommandEvent::Stderr(bytes) => {
                String::from_utf8_lossy(&bytes).into_owned()
            }
            CommandEvent::Terminated(_) => return None,
            _ => continue,
        };
        if let Some(url) = find_url(&line, suffix) {
            return Some(url);
        }
    }
    None
}

async fn open(
    app: &AppHandle,
    provider: Provider,
    port: u16,
) -> Result<(String, CommandChild), String> {
    let known_hosts = known_hosts_path(app)?;
    let args = vec![
        // No pty: this is not an interactive session, and a spawned child has
        // no terminal to allocate one against.
        "-T".to_string(),
        // Without this the first connection asks a question nothing can answer.
        "-o".to_string(),
        "StrictHostKeyChecking=accept-new".to_string(),
        "-o".to_string(),
        format!("UserKnownHostsFile={}", known_hosts.display()),
        "-o".to_string(),
        "ServerAliveInterval=30".to_string(),
        // Fail loudly instead of holding a session that forwards nothing.
        "-o".to_string(),
        "ExitOnForwardFailure=yes".to_string(),
        "-R".to_string(),
        format!("{}:127.0.0.1:{}", provider.remote_port, port),
        provider.destination.to_string(),
    ];

    let (mut events, child) = app
        .shell()
        .command("ssh")
        .args(args)
        .spawn()
        .map_err(|e| format!("could not start ssh: {e}"))?;

    match timeout(URL_TIMEOUT, read_url(&mut events, provider.url_suffix)).await {
        Ok(Some(url)) => {
            let handle = app.clone();
            let watched = url.clone();
            tauri::async_runtime::spawn(async move {
                // Keep draining: providers print a banner and an ANSI QR code,
                // and a full pipe would stall ssh once nobody is reading.
                while events.recv().await.is_some() {}
                // The stream ends when ssh exits. Without this the status
                // command would keep handing out a URL that is already dead.
                forget(&handle, &watched);
            });
            Ok((url, child))
        }
        Ok(None) => {
            let _ = child.kill();
            Err("ssh exited before providing a URL".to_string())
        }
        Err(_) => {
            let _ = child.kill();
            Err(format!("no URL within {} seconds", URL_TIMEOUT.as_secs()))
        }
    }
}

/// Open a tunnel to the share server, or return the one already running.
#[tauri::command]
pub async fn tunnel_start(
    app: AppHandle,
    state: State<'_, TunnelState>,
    port: u16,
) -> Result<String, String> {
    {
        let active = state.active.lock().map_err(|_| "tunnel state lost")?;
        if let Some(tunnel) = active.as_ref() {
            return Ok(tunnel.url.clone());
        }
    }

    let mut failures = Vec::new();
    for provider in PROVIDERS {
        match open(&app, provider, port).await {
            Ok((url, child)) => {
                let mut active = state.active.lock().map_err(|_| "tunnel state lost")?;
                *active = Some(ActiveTunnel {
                    url: url.clone(),
                    child,
                });
                return Ok(url);
            }
            Err(error) => failures.push(format!("{}: {error}", provider.name)),
        }
    }

    Err(format!(
        "Could not reach a tunnel provider. {}",
        failures.join("; ")
    ))
}

/// Close the tunnel. Safe to call when none is open.
#[tauri::command]
pub fn tunnel_stop(state: State<'_, TunnelState>) -> Result<(), String> {
    let mut active = state.active.lock().map_err(|_| "tunnel state lost")?;
    if let Some(tunnel) = active.take() {
        tunnel
            .child
            .kill()
            .map_err(|e| format!("could not stop the tunnel: {e}"))?;
    }
    Ok(())
}

/// The public URL, if a tunnel is open.
#[tauri::command]
pub fn tunnel_status(state: State<'_, TunnelState>) -> Result<Option<String>, String> {
    let active = state.active.lock().map_err(|_| "tunnel state lost")?;
    Ok(active.as_ref().map(|tunnel| tunnel.url.clone()))
}

/// Drop a tunnel from state, but only if it is still the current one.
///
/// A tunnel that died after a newer one replaced it must not clear the newer
/// one's URL, which is why this checks identity rather than blindly taking.
fn forget(app: &AppHandle, url: &str) {
    if let Some(state) = app.try_state::<TunnelState>() {
        if let Ok(mut active) = state.active.lock() {
            if active.as_ref().is_some_and(|tunnel| tunnel.url == url) {
                *active = None;
            }
        }
    }
}

/// Kill the tunnel on the way out, from outside a command context.
pub fn shutdown(app: &AppHandle) {
    if let Some(state) = app.try_state::<TunnelState>() {
        if let Ok(mut active) = state.active.lock() {
            if let Some(tunnel) = active.take() {
                let _ = tunnel.child.kill();
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::find_url;

    // Verbatim from localhost.run, which prints its own docs and social links
    // before the tunnel URL. Matching the first https:// token would take the
    // wrong one.
    const BANNER: &str =
        "Follow your favourite reverse tunnel at [https://twitter.com/localhost_run].";
    const DOCS: &str = "https://localhost.run/docs/";
    const ASSIGNED: &str =
        "d9b8d37391ddfb.lhr.life tunneled with tls termination, https://d9b8d37391ddfb.lhr.life";

    #[test]
    fn finds_the_assigned_url() {
        assert_eq!(
            find_url(ASSIGNED, ".lhr.life").as_deref(),
            Some("https://d9b8d37391ddfb.lhr.life")
        );
    }

    #[test]
    fn ignores_the_providers_own_links() {
        assert_eq!(find_url(BANNER, ".lhr.life"), None);
        assert_eq!(find_url(DOCS, ".lhr.life"), None);
    }

    #[test]
    fn tolerates_a_trailing_slash() {
        let line = "https://6bl6voavpt4jld4b7dq4bglbii.srv.us/";
        assert_eq!(
            find_url(line, ".srv.us").as_deref(),
            Some("https://6bl6voavpt4jld4b7dq4bglbii.srv.us")
        );
    }

    #[test]
    fn ignores_plain_http() {
        let line = "http://d9b8d37391ddfb.lhr.life";
        assert_eq!(find_url(line, ".lhr.life"), None);
    }
}
