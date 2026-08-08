//! Daily memory curation, driven from the desktop shell.
//!
//! The backend only curates when something asks it to, so nothing would ever
//! surface on a day with no import. This task asks once per launch (and again
//! on resume), then reports the result through the OS notification centre.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use serde::Deserialize;
use serde_json::{json, Value};
use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_notification::NotificationExt;
use tokio::time::sleep;

const BACKEND_URL: &str = "http://localhost:52123";

const REQUEST_TIMEOUT: Duration = Duration::from_secs(30);
/// The backend is spawned alongside the window and takes a while to bind.
const HEALTH_POLL: Duration = Duration::from_secs(2);
const HEALTH_TIMEOUT: Duration = Duration::from_secs(180);
/// Curating mid-index would score a half-written library, so wait it out.
const INDEXING_POLL: Duration = Duration::from_secs(20);
const INDEXING_TIMEOUT: Duration = Duration::from_secs(30 * 60);
const RUN_POLL: Duration = Duration::from_secs(5);
const RUN_TIMEOUT: Duration = Duration::from_secs(30 * 60);
/// How long the app must have gone unchecked before a focus re-runs the task.
const RESUME_INTERVAL: Duration = Duration::from_secs(6 * 60 * 60);

/// Guards against overlapping runs and throttles the resume check.
#[derive(Default)]
pub struct MemoryTaskState {
    running: AtomicBool,
    last_check: Mutex<Option<Instant>>,
    /// The last announcement, held until the frontend collects it. An event
    /// with nobody listening is simply lost, and the listener mounts after
    /// this task can already have emitted.
    pending: Mutex<Option<Value>>,
}

impl MemoryTaskState {
    fn is_due(&self) -> bool {
        match self.last_check.lock() {
            Ok(last) => last.is_none_or(|at| at.elapsed() >= RESUME_INTERVAL),
            Err(_) => false,
        }
    }

    fn mark_checked(&self) {
        if let Ok(mut last) = self.last_check.lock() {
            *last = Some(Instant::now());
        }
    }
}

/// `{success, message, data}` — the envelope every backend route returns.
#[derive(Deserialize)]
struct Envelope<T> {
    data: Option<T>,
}

#[derive(Deserialize)]
struct StatusData {
    run_status: Option<String>,
    /// Identifies *which* run is being reported; run_date is only ever today.
    run_started_at: Option<String>,
    indexing_busy: bool,
    memories_enabled: bool,
    notifications_enabled: bool,
}

#[derive(Deserialize)]
struct GenerateData {
    status: String,
    queued: bool,
}

#[derive(Deserialize)]
struct TodayData {
    memory: Option<MemorySummary>,
}

#[derive(Deserialize)]
struct MemorySummary {
    memory_id: String,
    title: String,
    subtitle: Option<String>,
    image_count: i64,
    video_count: i64,
    notified_at: Option<String>,
}

/// Run the curation check now, unless one is already in flight.
pub fn spawn_memory_task(app: AppHandle) {
    start(app, false);
}

/// Run the check on window focus, at most once per `RESUME_INTERVAL`. Covers
/// the app being left open across midnight.
pub fn check_on_resume(app: AppHandle) {
    start(app, true);
}

fn start(app: AppHandle, throttled: bool) {
    // try_state, not state: a window event must not panic the app if setup
    // never got as far as managing this.
    let Some(state) = app.try_state::<MemoryTaskState>() else {
        return;
    };
    if throttled && !state.is_due() {
        return;
    }
    if state.running.swap(true, Ordering::SeqCst) {
        return;
    }
    state.mark_checked();

    tauri::async_runtime::spawn(async move {
        run(&app).await;
        if let Some(state) = app.try_state::<MemoryTaskState>() {
            state.running.store(false, Ordering::SeqCst);
        }
    });
}

async fn run(app: &AppHandle) {
    let client = match reqwest::Client::builder().timeout(REQUEST_TIMEOUT).build() {
        Ok(client) => client,
        Err(e) => {
            eprintln!("[MEMORIES] Could not build an HTTP client: {e}");
            return;
        }
    };

    if !wait_for_backend(&client).await {
        println!("[MEMORIES] Backend never came up; skipping curation");
        return;
    }

    let status = match get_status(&client).await {
        Some(status) => status,
        None => return,
    };
    if !status.memories_enabled {
        return;
    }

    let status = match wait_while_indexing(&client, status).await {
        Some(status) => status,
        None => {
            println!("[MEMORIES] Library still indexing; skipping curation");
            return;
        }
    };

    let previous_run = status.run_started_at.clone();
    let queued = match generate(&client).await {
        Some(queued) => queued,
        None => return,
    };

    // Nothing was queued when today's run is already complete or already in
    // flight. Only our own run can be told apart by its start time; someone
    // else's is simply waited out.
    let status = if queued.queued {
        wait_for_run(&client, previous_run).await
    } else if queued.status == "running" {
        wait_for_run(&client, None).await
    } else {
        get_status(&client).await
    };

    let status = match status {
        Some(status) => status,
        None => return,
    };

    surface(app, &client, &status).await;
}

/// Announce the memory, once, through the card and the notification centre.
async fn surface(app: &AppHandle, client: &reqwest::Client, status: &StatusData) {
    let memory = match get_today(client).await {
        Some(memory) => memory,
        None => return,
    };

    // notified_at covers the card as well as the notification, since both say
    // the same thing. `/today` keeps returning a memory until it is viewed or
    // dismissed, so without this guard every launch and every resume announces
    // it again.
    if memory.notified_at.is_some() {
        return;
    }

    // Not gated on notifications_enabled: that preference is about OS alerts,
    // and it ships off. Announced whether or not the notification lands,
    // because desktop notification clicks are not dependable across platforms,
    // so the card is the path that always works.
    let announcement = json!({
        "memory_id": memory.memory_id,
        "title": memory.title,
        "subtitle": memory.subtitle,
        "image_count": memory.image_count,
        "video_count": memory.video_count,
    });

    // Stored before it is emitted, and collected by the listener on mount.
    // On a launch where the backend is already up this whole task can finish
    // before React has mounted, and the event alone would be lost while
    // notified_at below still recorded it as delivered.
    if let Some(state) = app.try_state::<MemoryTaskState>() {
        if let Ok(mut pending) = state.pending.lock() {
            *pending = Some(announcement.clone());
        }
    }
    let _ = app.emit("memory:pending", announcement);

    if status.notifications_enabled {
        notify(app, &memory);
    }

    // Recorded even when the notification failed: the card still went out.
    mark_notified(client, &memory.memory_id).await;
}

fn notify(app: &AppHandle, memory: &MemorySummary) {
    let count = memory.image_count + memory.video_count;
    let body = match memory.subtitle.as_deref() {
        Some(subtitle) => format!("{} · {} · {} items", memory.title, subtitle, count),
        None => format!("{} · {} items", memory.title, count),
    };

    // No permission check: the plugin's desktop implementation returns Granted
    // unconditionally, and the prompt that does exist is the webview one the
    // settings switch raises. A mobile target would need one here.
    if let Err(e) = app
        .notification()
        .builder()
        .title("Your Daily Memory is Ready")
        .body(body)
        .show()
    {
        eprintln!("[MEMORIES] Could not show the notification: {e}");
    }
}

/// Hand over an announcement the frontend was not yet listening for. Called by
/// the listener on mount, which is what makes delivery independent of whether
/// the webview beat the task.
#[tauri::command]
pub fn take_pending_memory(app: AppHandle) -> Option<Value> {
    let state = app.try_state::<MemoryTaskState>()?;
    let mut pending = state.pending.lock().ok()?;
    pending.take()
}

/// Focus the window and route the app to a memory. Invoked by the in-app card,
/// and the single entry point any notification-click handler should use.
#[tauri::command]
pub fn open_memory(app: AppHandle, memory_id: String) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
    app.emit("memory:open", json!({ "memory_id": memory_id }))
        .map_err(|e| e.to_string())
}

async fn wait_for_backend(client: &reqwest::Client) -> bool {
    let deadline = Instant::now() + HEALTH_TIMEOUT;
    loop {
        if let Ok(response) = client.get(format!("{BACKEND_URL}/health")).send().await {
            if response.status().is_success() {
                return true;
            }
        }
        if Instant::now() >= deadline {
            return false;
        }
        sleep(HEALTH_POLL).await;
    }
}

/// Poll until the library is idle. `None` means it never settled.
async fn wait_while_indexing(client: &reqwest::Client, status: StatusData) -> Option<StatusData> {
    let mut status = status;
    let deadline = Instant::now() + INDEXING_TIMEOUT;
    while status.indexing_busy {
        if Instant::now() >= deadline {
            return None;
        }
        sleep(INDEXING_POLL).await;
        status = get_status(client).await?;
        if !status.memories_enabled {
            return None;
        }
    }
    Some(status)
}

/// Poll until the run we queued reaches a terminal state. `None` means it
/// never did, so there is nothing to announce.
async fn wait_for_run(
    client: &reqwest::Client,
    previous_run: Option<String>,
) -> Option<StatusData> {
    let deadline = Instant::now() + RUN_TIMEOUT;
    loop {
        sleep(RUN_POLL).await;
        let status = get_status(client).await?;

        // A run that finished before we polled reports 'complete' either way,
        // so the start time is what tells our run from an earlier one today.
        let is_ours = status.run_started_at != previous_run;
        let settled = matches!(
            status.run_status.as_deref(),
            Some("complete") | Some("failed")
        );
        if is_ours && settled {
            return Some(status);
        }
        if Instant::now() >= deadline {
            return None;
        }
    }
}

async fn get_status(client: &reqwest::Client) -> Option<StatusData> {
    get(client, "/memories/status").await
}

async fn get_today(client: &reqwest::Client) -> Option<MemorySummary> {
    let today: TodayData = get(client, "/memories/today").await?;
    today.memory
}

async fn get<T: for<'de> Deserialize<'de>>(client: &reqwest::Client, path: &str) -> Option<T> {
    let response = client
        .get(format!("{BACKEND_URL}{path}"))
        .send()
        .await
        .map_err(|e| eprintln!("[MEMORIES] GET {path} failed: {e}"))
        .ok()?;

    response
        .json::<Envelope<T>>()
        .await
        .map_err(|e| eprintln!("[MEMORIES] GET {path} returned unreadable JSON: {e}"))
        .ok()?
        .data
}

async fn generate(client: &reqwest::Client) -> Option<GenerateData> {
    // No `force`: the user's preference decides, and a run already complete
    // for today is not worth redoing.
    let response = client
        .post(format!("{BACKEND_URL}/memories/generate"))
        .json(&json!({}))
        .send()
        .await
        .map_err(|e| eprintln!("[MEMORIES] Could not queue a curation run: {e}"))
        .ok()?;

    if !response.status().is_success() {
        eprintln!("[MEMORIES] Generate returned {}", response.status());
        return None;
    }

    response
        .json::<Envelope<GenerateData>>()
        .await
        .map_err(|e| eprintln!("[MEMORIES] Generate returned unreadable JSON: {e}"))
        .ok()?
        .data
}

async fn mark_notified(client: &reqwest::Client, memory_id: &str) {
    if let Err(e) = client
        .patch(format!("{BACKEND_URL}/memories/{memory_id}"))
        .json(&json!({ "notified": true }))
        .send()
        .await
    {
        eprintln!("[MEMORIES] Could not record the notification: {e}");
    }
}
