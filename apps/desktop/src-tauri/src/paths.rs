use serde::{Deserialize, Serialize};
use std::{
    env,
    fs,
    path::{Path, PathBuf},
};
use tauri::{path::BaseDirectory, AppHandle, Manager};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimePaths {
    pub data_root: PathBuf,
    pub profiles_dir: PathBuf,
    pub exports_dir: PathBuf,
    pub cache_dir: PathBuf,
    pub logs_dir: PathBuf,
    pub temp_dir: PathBuf,
    pub is_development: bool,
}

pub fn resolve_runtime_paths(app: &AppHandle) -> Result<RuntimePaths, String> {
    if let Some(dev_root) = discover_development_data_root() {
        return Ok(build_paths(dev_root, true));
    }

    let data_root = app
        .path()
        .resolve("Home Voice Studio", BaseDirectory::AppLocalData)
        .map_err(|err| err.to_string())?;

    Ok(build_paths(data_root, false))
}

pub fn ensure_runtime_directories(paths: &RuntimePaths) -> Result<(), String> {
    for path in [
        &paths.data_root,
        &paths.profiles_dir,
        &paths.exports_dir,
        &paths.cache_dir,
        &paths.logs_dir,
        &paths.temp_dir,
    ] {
        fs::create_dir_all(path).map_err(|err| err.to_string())?;
    }

    Ok(())
}

fn build_paths(data_root: PathBuf, is_development: bool) -> RuntimePaths {
    let profiles_dir = data_root.join("profiles");
    let exports_dir = data_root.join("exports");
    let cache_dir = data_root.join("cache");
    let logs_dir = data_root.join("logs");
    let temp_dir = cache_dir.join("temp");

    RuntimePaths {
        data_root,
        profiles_dir,
        exports_dir,
        cache_dir,
        logs_dir,
        temp_dir,
        is_development,
    }
}

fn discover_development_data_root() -> Option<PathBuf> {
    for key in ["HOME_VOICE_STUDIO_DATA_ROOT", "HVS_DATA_ROOT"] {
        if let Ok(override_root) = env::var(key) {
            let path = PathBuf::from(override_root);
            if path.exists() {
                return Some(path);
            }
        }
    }

    let manifest_candidate = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../data");
    if manifest_candidate.exists() {
        return manifest_candidate.canonicalize().ok().or(Some(manifest_candidate));
    }

    None
}

#[allow(dead_code)]
fn _is_probably_directory(path: &Path) -> bool {
    path.is_dir()
}
