use crate::paths::RuntimePaths;
use serde::{Deserialize, Serialize};
use std::{
    env,
    fs,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::Mutex,
    time::{Duration, Instant},
};
use tauri::{AppHandle, Manager, State};

pub const DEFAULT_INFERENCE_HOST: &str = "127.0.0.1";
pub const DEFAULT_INFERENCE_PORT: u16 = 43127;
const HEALTH_TIMEOUT: Duration = Duration::from_secs(25);
const SIDECAR_BINARY_STEM: &str = "home-voice-studio-inference";

#[derive(Debug)]
pub struct HostState {
    pub runtime_paths: RuntimePaths,
    pub sidecar: Mutex<Option<RunningSidecar>>,
}

impl HostState {
    pub fn new(runtime_paths: RuntimePaths) -> Self {
        Self {
            runtime_paths,
            sidecar: Mutex::new(None),
        }
    }
}

impl Drop for HostState {
    fn drop(&mut self) {
        if let Ok(mut guard) = self.sidecar.lock() {
            if let Some(mut running) = guard.take() {
                let _ = running.child.kill();
                let _ = running.child.wait();
            }
        }
    }
}

#[derive(Debug)]
pub struct RunningSidecar {
    pub child: Child,
    pub base_url: String,
    pub started_at: Instant,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SidecarStatus {
    pub running: bool,
    pub base_url: String,
    pub host: String,
    pub port: u16,
}

#[derive(Debug)]
enum SidecarLaunch {
    BundledBinary(PathBuf),
    PythonModule { python: String, workdir: PathBuf },
}

pub fn base_url(port: u16) -> String {
    format!("http://{}:{}", DEFAULT_INFERENCE_HOST, port)
}

pub async fn ensure_running(
    app: AppHandle,
    state: State<'_, HostState>,
) -> Result<SidecarStatus, String> {
    if let Some(status) = try_reuse_existing(app.clone(), &state).await? {
        return Ok(status);
    }

    let port = DEFAULT_INFERENCE_PORT;
    let base_url = base_url(port);
    configure_sidecar_environment(&state.runtime_paths, port);
    let child = spawn_sidecar_process(&app, &state.runtime_paths, port)?;

    {
        let mut guard = state.sidecar.lock().map_err(|err| err.to_string())?;
        if let Some(existing) = guard.take() {
            let _ = existing.child.kill();
        }
        *guard = Some(RunningSidecar {
            child,
            base_url: base_url.clone(),
            started_at: Instant::now(),
        });
    }

    wait_for_health(&base_url).await?;

    Ok(SidecarStatus {
        running: true,
        base_url,
        host: DEFAULT_INFERENCE_HOST.to_string(),
        port,
    })
}

pub async fn health(
    app: AppHandle,
    state: State<'_, HostState>,
) -> Result<serde_json::Value, String> {
    ensure_running(app, state).await?;
    let base_url = {
        let guard = state.sidecar.lock().map_err(|err| err.to_string())?;
        guard
            .as_ref()
            .map(|running| running.base_url.clone())
            .ok_or_else(|| String::from("sidecar not running"))?
    };

    request_json(reqwest::Method::GET, &format!("{base_url}/health"), None).await
}

pub async fn request_route(
    app: AppHandle,
    state: State<'_, HostState>,
    request: SidecarRouteRequest,
) -> Result<serde_json::Value, String> {
    ensure_running(app, state).await?;
    let base_url = {
        let guard = state.sidecar.lock().map_err(|err| err.to_string())?;
        guard
            .as_ref()
            .map(|running| running.base_url.clone())
            .ok_or_else(|| String::from("sidecar not running"))?
    };

    let method = reqwest::Method::from_bytes(request.method.as_bytes())
        .map_err(|err| err.to_string())?;
    let url = format!("{base_url}{}", normalize_route(&request.path));
    request_json(method, &url, request.body).await
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SidecarRouteRequest {
    pub method: String,
    pub path: String,
    pub body: Option<serde_json::Value>,
}

async fn try_reuse_existing(
    _app: AppHandle,
    state: &State<'_, HostState>,
) -> Result<Option<SidecarStatus>, String> {
    let base_url = {
        let guard = state.sidecar.lock().map_err(|err| err.to_string())?;
        guard.as_ref().map(|running| running.base_url.clone())
    };

    if let Some(base_url) = base_url {
        if request_json(reqwest::Method::GET, &format!("{base_url}/health"), None)
            .await
            .is_ok()
        {
            return Ok(Some(SidecarStatus {
                running: true,
                base_url,
                host: DEFAULT_INFERENCE_HOST.to_string(),
                port: DEFAULT_INFERENCE_PORT,
            }));
        }
    }

    {
        let mut guard = state.sidecar.lock().map_err(|err| err.to_string())?;
        if let Some(existing) = guard.take() {
            let _ = existing.child.kill();
        }
    }
    Ok(None)
}

async fn wait_for_health(base_url: &str) -> Result<(), String> {
    let deadline = Instant::now() + HEALTH_TIMEOUT;

    loop {
        if request_json(reqwest::Method::GET, &format!("{base_url}/health"), None)
            .await
            .is_ok()
        {
            return Ok(());
        }

        if Instant::now() >= deadline {
            return Err(String::from("sidecar did not become healthy in time"));
        }

        tokio::time::sleep(Duration::from_millis(400)).await;
    }
}

fn configure_sidecar_environment(paths: &RuntimePaths, port: u16) {
    env::set_var("HVS_HOST", DEFAULT_INFERENCE_HOST);
    env::set_var("HVS_PORT", port.to_string());
    env::set_var("HVS_DATA_ROOT", &paths.data_root);
    env::set_var("HOME_VOICE_STUDIO_DATA_ROOT", &paths.data_root);
}

fn spawn_sidecar_process(
    app: &AppHandle,
    paths: &RuntimePaths,
    port: u16,
) -> Result<Child, String> {
    let launch = resolve_sidecar_launch(app, paths)?;
    let mut command = match launch {
        SidecarLaunch::BundledBinary(executable) => {
            let mut command = Command::new(executable);
            command
                .arg("--host")
                .arg(DEFAULT_INFERENCE_HOST)
                .arg("--port")
                .arg(port.to_string())
                .arg("--log-level")
                .arg("info")
                .arg("--data-root")
                .arg(&paths.data_root);
            command
        }
        SidecarLaunch::PythonModule { python, workdir } => {
            let mut command = Command::new(python);
            command
                .current_dir(workdir)
                .arg("-m")
                .arg("app.cli")
                .arg("--host")
                .arg(DEFAULT_INFERENCE_HOST)
                .arg("--port")
                .arg(port.to_string())
                .arg("--log-level")
                .arg("info")
                .arg("--data-root")
                .arg(&paths.data_root);
            command
        }
    };

    command
        .stdin(Stdio::null())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit());

    command.spawn().map_err(|err| err.to_string())
}

fn resolve_sidecar_launch(app: &AppHandle, paths: &RuntimePaths) -> Result<SidecarLaunch, String> {
    if let Some(executable) = resolve_explicit_sidecar_binary() {
        return Ok(SidecarLaunch::BundledBinary(executable));
    }

    if let Some(executable) = resolve_bundled_sidecar_binary(app) {
        return Ok(SidecarLaunch::BundledBinary(executable));
    }

    if paths.is_development {
        return Ok(SidecarLaunch::PythonModule {
            python: resolve_python_executable()?,
            workdir: resolve_inference_workdir()?,
        });
    }

    Err(String::from(
        "could not locate a bundled inference sidecar binary; set HVS_SIDECAR_BIN or rebuild the desktop package with the sidecar included",
    ))
}

fn resolve_explicit_sidecar_binary() -> Option<PathBuf> {
    for key in ["HVS_SIDECAR_BIN", "HOME_VOICE_STUDIO_SIDECAR_BIN"] {
        let Some(path) = env::var_os(key).map(PathBuf::from) else {
            continue;
        };
        if path.exists() {
            return Some(path);
        }
    }

    None
}

fn resolve_bundled_sidecar_binary(app: &AppHandle) -> Option<PathBuf> {
    let mut roots = Vec::new();

    if let Ok(resource_dir) = app.path().resource_dir() {
        roots.push(resource_dir);
    }

    if let Ok(current_exe) = env::current_exe() {
        if let Some(parent) = current_exe.parent() {
            roots.push(parent.to_path_buf());
            roots.push(parent.join("../Resources"));
            roots.push(parent.join("../Frameworks"));
        }
    }

    for root in roots {
        if let Some(executable) = find_sidecar_binary_in_root(&root) {
            return Some(executable);
        }
    }

    None
}

fn find_sidecar_binary_in_root(root: &Path) -> Option<PathBuf> {
    let search_dirs = [root.to_path_buf(), root.join("binaries")];

    for dir in search_dirs {
        if let Some(executable) = find_sidecar_binary_in_dir(&dir) {
            return Some(executable);
        }
    }

    None
}

fn find_sidecar_binary_in_dir(dir: &Path) -> Option<PathBuf> {
    if !dir.exists() {
        return None;
    }

    let exact_names = [
        SIDECAR_BINARY_STEM.to_string(),
        format!("{SIDECAR_BINARY_STEM}.exe"),
    ];

    for name in exact_names {
        let candidate = dir.join(name);
        if candidate.is_file() {
            return Some(candidate);
        }
    }

    let entries = fs::read_dir(dir).ok()?;
    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let Some(file_name) = path.file_name().and_then(|value| value.to_str()) else {
            continue;
        };
        if file_name == SIDECAR_BINARY_STEM
            || file_name == format!("{SIDECAR_BINARY_STEM}.exe")
            || file_name.starts_with(&format!("{SIDECAR_BINARY_STEM}-"))
        {
            return Some(path);
        }
    }

    None
}

fn resolve_python_executable() -> Result<String, String> {
    let candidates = [
        env::var("HVS_PYTHON").ok(),
        env::var("HOME_VOICE_STUDIO_PYTHON").ok(),
        env::var("PYTHON").ok(),
        Some(String::from("python3")),
        Some(String::from("python")),
    ];

    for candidate in candidates.into_iter().flatten() {
        if python_supports_sidecar(&candidate) {
            return Ok(candidate);
        }
    }

    Err(String::from(
        "could not locate a Python executable with uvicorn and fastapi available for the sidecar",
    ))
}

fn python_supports_sidecar(candidate: &str) -> bool {
    Command::new(candidate)
        .arg("-c")
        .arg("import fastapi, uvicorn")
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

fn resolve_inference_workdir() -> Result<PathBuf, String> {
    if let Ok(override_dir) = env::var("HVS_INFERENCE_WORKDIR") {
        let path = PathBuf::from(override_dir);
        if path.exists() {
            return Ok(path);
        }
    }

    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../services/inference")
        .canonicalize()
        .map_err(|err| err.to_string())
}

async fn request_json(
    method: reqwest::Method,
    url: &str,
    body: Option<serde_json::Value>,
) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(30))
        .build()
        .map_err(|err| err.to_string())?;

    let mut request = client.request(method, url);
    if let Some(body) = body {
        request = request.json(&body);
    }

    let response = request.send().await.map_err(|err| err.to_string())?;
    let status = response.status();
    let text = response.text().await.map_err(|err| err.to_string())?;

    if !status.is_success() {
        return Err(format!("sidecar request failed ({status}): {text}"));
    }

    if text.trim().is_empty() {
        return Ok(serde_json::Value::Null);
    }

    serde_json::from_str(&text).or_else(|_| Ok(serde_json::Value::String(text)))
}

fn normalize_route(route: &str) -> String {
    if route.starts_with('/') {
        route.to_string()
    } else {
        format!("/{route}")
    }
}
