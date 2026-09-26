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
use tokio::sync::Mutex as AsyncMutex;
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

/// The part of a spawned process this module actually needs.
///
/// Named so the lifecycle can be exercised without spawning ssh; the real
/// implementation is the shell plugin's child.
pub trait TunnelChild: Send + 'static {
    fn pid(&self) -> u32;
    fn kill(self) -> Result<(), String>;
}

impl TunnelChild for CommandChild {
    fn pid(&self) -> u32 {
        CommandChild::pid(self)
    }

    fn kill(self) -> Result<(), String> {
        CommandChild::kill(self).map_err(|e| e.to_string())
    }
}

struct ActiveTunnel<C: TunnelChild> {
    /// None until the provider announces one. The child is tracked before then
    /// so that an exit during discovery still has something to kill.
    url: Option<String>,
    child: C,
}

/// The tracked child, and whether the app has begun shutting down.
///
/// Both live under one lock on purpose. Kept apart, a shutdown could land
/// between a child being spawned and being tracked, find nothing to kill, and
/// let the start install an ssh process that then outlives the application.
struct Tracked<C: TunnelChild> {
    tunnel: Option<ActiveTunnel<C>>,
    closed: bool,
}

pub struct TunnelStateOf<C: TunnelChild> {
    /// Held across an entire start or stop, spawn included. Without it two
    /// concurrent starts could both find no tunnel, both spawn a child, and
    /// leave whichever installed first running with nothing holding its
    /// handle — an ssh process nobody can stop.
    lifecycle: AsyncMutex<()>,
    tracked: Mutex<Tracked<C>>,
}

pub type TunnelState = TunnelStateOf<CommandChild>;

impl<C: TunnelChild> TunnelStateOf<C> {
    pub fn new() -> Self {
        Self {
            lifecycle: AsyncMutex::new(()),
            tracked: Mutex::new(Tracked {
                tunnel: None,
                closed: false,
            }),
        }
    }

    fn current_url(&self) -> Option<String> {
        self.tracked
            .lock()
            .ok()
            .and_then(|tracked| tracked.tunnel.as_ref().and_then(|t| t.url.clone()))
    }

    /// Start tracking a child, before it has announced anything.
    ///
    /// Refuses once shutdown has been requested, killing the child rather than
    /// storing it: by then nothing will come back to stop it.
    fn track(&self, child: C) -> Result<(), String> {
        let mut tracked = self.tracked.lock().map_err(|_| "tunnel state lost")?;
        if tracked.closed {
            drop(tracked);
            let _ = child.kill();
            return Err("PictoPy is shutting down".to_string());
        }
        tracked.tunnel = Some(ActiveTunnel { url: None, child });
        Ok(())
    }

    fn announce(&self, url: &str) -> Result<(), String> {
        let mut tracked = self.tracked.lock().map_err(|_| "tunnel state lost")?;
        if let Some(tunnel) = tracked.tunnel.as_mut() {
            tunnel.url = Some(url.to_string());
        }
        Ok(())
    }

    /// Kill whatever is tracked and stop tracking it.
    ///
    /// The pid is read first because killing consumes the handle: it cannot be
    /// put back for a retry, so a failure has to name the process instead.
    fn stop(&self) -> Result<(), String> {
        self.take_and_kill(false)
    }

    /// Stop, and refuse to track anything spawned from here on.
    fn close_permanently(&self) -> Result<(), String> {
        self.take_and_kill(true)
    }

    fn take_and_kill(&self, closing: bool) -> Result<(), String> {
        let tunnel = {
            let mut tracked = self.tracked.lock().map_err(|_| "tunnel state lost")?;
            if closing {
                tracked.closed = true;
            }
            tracked.tunnel.take()
        };
        let Some(tunnel) = tunnel else {
            return Ok(());
        };
        let pid = tunnel.child.pid();
        tunnel.child.kill().map_err(|e| {
            format!("could not stop the tunnel (ssh pid {pid} may still be running): {e}")
        })
    }

    /// Drop a tunnel from state, but only if it is still the current one.
    ///
    /// A tunnel that died after a newer one replaced it must not clear the
    /// newer one's URL, which is why this checks identity rather than taking.
    fn forget(&self, url: &str) {
        if let Ok(mut tracked) = self.tracked.lock() {
            let matches = tracked
                .tunnel
                .as_ref()
                .and_then(|tunnel| tunnel.url.as_deref())
                .is_some_and(|current| current == url);
            if matches {
                tracked.tunnel = None;
            }
        }
    }
}

impl<C: TunnelChild> Default for TunnelStateOf<C> {
    fn default() -> Self {
        Self::new()
    }
}

/// The public URL in a line of provider output, if there is one.
///
/// Split on whitespace rather than pattern-matching the sentence around it: the
/// wording is the provider's to change, and one has already been observed
/// printing something different from its own documentation. Each event is a
/// whole line, because the shell plugin frames process output with read_line.
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

fn spawn_ssh(
    app: &AppHandle,
    provider: Provider,
    port: u16,
) -> Result<(Receiver<CommandEvent>, CommandChild), String> {
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

    app.shell()
        .command("ssh")
        .args(args)
        .spawn()
        .map_err(|e| format!("could not start ssh: {e}"))
}

/// Open a tunnel to the share server, or return the one already running.
#[tauri::command]
pub async fn tunnel_start(
    app: AppHandle,
    state: State<'_, TunnelState>,
    port: u16,
) -> Result<String, String> {
    let _lifecycle = state.lifecycle.lock().await;

    // Re-checked while holding the lock, not before taking it.
    if let Some(url) = state.current_url() {
        return Ok(url);
    }

    let mut failures = Vec::new();
    for provider in PROVIDERS {
        let (mut events, child) = match spawn_ssh(&app, provider, port) {
            Ok(spawned) => spawned,
            Err(error) => {
                failures.push(format!("{}: {error}", provider.name));
                continue;
            }
        };

        // Tracked before the URL arrives. If the app exits while we are still
        // waiting, shutdown has a handle to kill instead of leaving an ssh
        // child forwarding an album with nothing owning it.
        state.track(child)?;

        match timeout(URL_TIMEOUT, read_url(&mut events, provider.url_suffix)).await {
            Ok(Some(url)) => {
                state.announce(&url)?;
                let handle = app.clone();
                let watched = url.clone();
                tauri::async_runtime::spawn(async move {
                    // Keep draining: providers print a banner and an ANSI QR
                    // code, and a full pipe would stall ssh once nobody reads.
                    while events.recv().await.is_some() {}
                    // The stream ends when ssh exits. Without this the status
                    // command would keep handing out a URL that is already dead.
                    if let Some(state) = handle.try_state::<TunnelState>() {
                        state.forget(&watched);
                    }
                });
                return Ok(url);
            }
            Ok(None) => {
                let _ = state.stop();
                failures.push(format!(
                    "{}: ssh exited before providing a URL",
                    provider.name
                ));
            }
            Err(_) => {
                let _ = state.stop();
                failures.push(format!(
                    "{}: no URL within {} seconds",
                    provider.name,
                    URL_TIMEOUT.as_secs()
                ));
            }
        }
    }

    Err(format!(
        "Could not reach a tunnel provider. {}",
        failures.join("; ")
    ))
}

/// Close the tunnel. Safe to call when none is open.
#[tauri::command]
pub async fn tunnel_stop(state: State<'_, TunnelState>) -> Result<(), String> {
    let _lifecycle = state.lifecycle.lock().await;
    state.stop()
}

/// The public URL, if a tunnel is open and has announced one.
#[tauri::command]
pub fn tunnel_status(state: State<'_, TunnelState>) -> Result<Option<String>, String> {
    Ok(state.current_url())
}

/// Kill the tunnel on the way out, from outside a command context.
///
/// Deliberately does not take the lifecycle lock: this runs on the exit path,
/// where blocking on an in-flight start would be worse than racing it. Racing
/// it is safe because the refusal is recorded under the same lock the start
/// uses to track its child, so a child spawned but not yet tracked is killed
/// by whichever of the two arrives second.
pub fn shutdown(app: &AppHandle) {
    if let Some(state) = app.try_state::<TunnelState>() {
        let _ = state.close_permanently();
    }
}

#[cfg(test)]
mod tests {
    use super::{find_url, TunnelChild, TunnelStateOf};
    use std::sync::atomic::{AtomicBool, Ordering};
    use std::sync::Arc;

    struct FakeChild {
        pid: u32,
        killed: Arc<AtomicBool>,
        refuses: bool,
    }

    impl TunnelChild for FakeChild {
        fn pid(&self) -> u32 {
            self.pid
        }

        fn kill(self) -> Result<(), String> {
            self.killed.store(true, Ordering::SeqCst);
            if self.refuses {
                return Err("access denied".to_string());
            }
            Ok(())
        }
    }

    fn child(killed: &Arc<AtomicBool>, refuses: bool) -> FakeChild {
        FakeChild {
            pid: 4242,
            killed: Arc::clone(killed),
            refuses,
        }
    }

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

    #[test]
    fn stopping_kills_the_child_and_clears_the_state() {
        let killed = Arc::new(AtomicBool::new(false));
        let state = TunnelStateOf::new();
        state.track(child(&killed, false)).unwrap();
        state.announce("https://one.lhr.life").unwrap();

        assert!(state.stop().is_ok());
        assert!(killed.load(Ordering::SeqCst));
        assert_eq!(state.current_url(), None);
    }

    #[test]
    fn stopping_nothing_is_not_an_error() {
        let state: TunnelStateOf<FakeChild> = TunnelStateOf::new();
        assert!(state.stop().is_ok());
    }

    // A child that refused to die is the one case worth naming: the handle is
    // consumed by the attempt, so the pid is all the caller has left to act on.
    #[test]
    fn a_refused_kill_reports_the_process() {
        let killed = Arc::new(AtomicBool::new(false));
        let state = TunnelStateOf::new();
        state.track(child(&killed, true)).unwrap();

        let error = state.stop().unwrap_err();
        assert!(error.contains("4242"), "{error}");
        assert!(error.contains("may still be running"), "{error}");
    }

    // Exit can land between ssh being spawned and the handle being tracked.
    // Whichever arrives second has to kill it, or the process outlives the app
    // with an album still forwarding.
    #[test]
    fn a_child_spawned_during_shutdown_is_killed_not_stored() {
        let killed = Arc::new(AtomicBool::new(false));
        let state = TunnelStateOf::new();

        state.close_permanently().unwrap();
        let refused = state.track(child(&killed, false));

        assert!(refused.is_err(), "tracking must not succeed after shutdown");
        assert!(killed.load(Ordering::SeqCst), "the child is killed instead");
        assert_eq!(state.current_url(), None);
    }

    // The gap that let an exit during startup orphan an ssh process.
    #[test]
    fn a_child_is_killable_before_it_announces_a_url() {
        let killed = Arc::new(AtomicBool::new(false));
        let state = TunnelStateOf::new();
        state.track(child(&killed, false)).unwrap();

        assert_eq!(state.current_url(), None, "nothing to advertise yet");
        assert!(state.stop().is_ok());
        assert!(killed.load(Ordering::SeqCst), "the child still gets killed");
    }

    #[test]
    fn a_dead_tunnel_does_not_clear_the_one_that_replaced_it() {
        let killed = Arc::new(AtomicBool::new(false));
        let state = TunnelStateOf::new();
        state.track(child(&killed, false)).unwrap();
        state.announce("https://second.lhr.life").unwrap();

        state.forget("https://first.lhr.life");

        assert_eq!(
            state.current_url().as_deref(),
            Some("https://second.lhr.life")
        );
    }

    #[test]
    fn a_tunnel_forgets_itself_when_it_dies() {
        let killed = Arc::new(AtomicBool::new(false));
        let state = TunnelStateOf::new();
        state.track(child(&killed, false)).unwrap();
        state.announce("https://only.lhr.life").unwrap();

        state.forget("https://only.lhr.life");

        assert_eq!(state.current_url(), None);
    }
}
