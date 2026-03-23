use crate::paths::RuntimePaths;
use serde::{Deserialize, Serialize};
use std::{
    env,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::Mutex,
    time::{Duration, Instant},
};
use tauri::{AppHandle, State};

pub const DEFAULT_INFERENCE_HOST: &str = "127.0.0.1";
pub const DEFAULT_INFERENCE_PORT: u16 = 43127;
const HEALTH_TIMEOUT: Duration = Duration::from_secs(25);

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
    let child = spawn_sidecar_process(port)?;

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

fn spawn_sidecar_process(port: u16) -> Result<Child, String> {
    let python = resolve_python_executable()?;
    let workdir = resolve_inference_workdir()?;
    let mut command = Command::new(python);
    command
        .current_dir(workdir)
        .arg("-m")
        .arg("uvicorn")
        .arg("app.main:app")
        .arg("--host")
        .arg(DEFAULT_INFERENCE_HOST)
        .arg("--port")
        .arg(port.to_string())
        .arg("--log-level")
        .arg("info")
        .stdin(Stdio::null())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit());

    command.spawn().map_err(|err| err.to_string())
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
