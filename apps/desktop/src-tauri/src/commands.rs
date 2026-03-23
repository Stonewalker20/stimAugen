use crate::sidecar::{self, HostState, SidecarRouteRequest};
use serde::{Deserialize, Serialize};
use tauri::{AppHandle, State};
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons, MessageDialogKind};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DesktopFilter {
    pub name: String,
    pub extensions: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SaveDialogRequest {
    pub title: Option<String>,
    pub default_name: Option<String>,
    pub default_directory: Option<String>,
    pub filters: Option<Vec<DesktopFilter>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PickerRequest {
    pub title: Option<String>,
    pub default_directory: Option<String>,
    pub filters: Vec<DesktopFilter>,
}

#[tauri::command]
pub fn get_app_paths(state: State<'_, HostState>) -> Result<crate::paths::RuntimePaths, String> {
    Ok(state.runtime_paths.clone())
}

#[tauri::command]
pub async fn pick_audio_file(app: AppHandle) -> Result<Option<String>, String> {
    pick_single_audio_file(app, false).await
}

#[tauri::command]
pub async fn pick_audio_files(app: AppHandle) -> Result<Vec<String>, String> {
    let app_handle = app.clone();
    tauri::async_runtime::spawn_blocking(move || {
        let files = app_handle
            .dialog()
            .file()
            .set_title("Choose audio files")
            .add_filter(
                "Audio",
                &["wav", "mp3", "flac", "m4a", "aac", "ogg", "aiff"],
            )
            .blocking_pick_files();

        Ok(files
            .unwrap_or_default()
            .into_iter()
            .filter_map(file_path_to_string)
            .collect::<Vec<_>>())
    })
    .await
    .map_err(|err| err.to_string())?
}

#[tauri::command]
pub async fn save_export_file(
    app: AppHandle,
    request: SaveDialogRequest,
) -> Result<Option<String>, String> {
    let app_handle = app.clone();
    tauri::async_runtime::spawn_blocking(move || {
        let mut builder = app_handle.dialog().file();
        if let Some(title) = request.title {
            builder = builder.set_title(title);
        }

        if let Some(default_directory) = request.default_directory {
            builder = builder.set_directory(default_directory);
        }

        if let Some(default_name) = request.default_name {
            builder = builder.set_file_name(default_name);
        }

        for filter in request.filters.unwrap_or_default() {
            let extensions: Vec<&str> = filter.extensions.iter().map(String::as_str).collect();
            builder = builder.add_filter(filter.name, &extensions);
        }

        Ok(builder
            .blocking_save_file()
            .and_then(file_path_to_string))
    })
    .await
    .map_err(|err| err.to_string())?
}

#[tauri::command]
pub async fn confirm_voice_cloning(app: AppHandle) -> Result<bool, String> {
    let app_handle = app.clone();
    tauri::async_runtime::spawn_blocking(move || {
        Ok(app_handle
            .dialog()
            .message(
                "Creating a voice profile requires explicit permission for voice cloning style processing.",
            )
            .buttons(MessageDialogButtons::OkCancelCustom(
                "I understand".to_string(),
                "Cancel".to_string(),
            ))
            .kind(MessageDialogKind::Warning)
            .blocking_show())
    })
    .await
    .map_err(|err| err.to_string())?
}

#[tauri::command]
pub async fn ensure_sidecar_running(
    app: AppHandle,
    state: State<'_, HostState>,
) -> Result<sidecar::SidecarStatus, String> {
    sidecar::ensure_running(app, state).await
}

#[tauri::command]
pub async fn sidecar_health(
    app: AppHandle,
    state: State<'_, HostState>,
) -> Result<serde_json::Value, String> {
    sidecar::health(app, state).await
}

#[tauri::command]
pub async fn call_sidecar_route(
    app: AppHandle,
    state: State<'_, HostState>,
    request: SidecarRouteRequest,
) -> Result<serde_json::Value, String> {
    sidecar::request_route(app, state, request).await
}

async fn pick_single_audio_file(app: AppHandle, allow_multiple: bool) -> Result<Option<String>, String> {
    let app_handle = app.clone();
    tauri::async_runtime::spawn_blocking(move || {
        let builder = app_handle
            .dialog()
            .file()
            .set_title("Choose an audio file")
            .add_filter(
                "Audio",
                &["wav", "mp3", "flac", "m4a", "aac", "ogg", "aiff"],
            );

        if allow_multiple {
            let files = builder.blocking_pick_files();
            return Ok(files
                .and_then(|files| files.into_iter().next())
                .and_then(file_path_to_string));
        }

        Ok(builder.blocking_pick_file().and_then(file_path_to_string))
    })
    .await
    .map_err(|err| err.to_string())?
}

fn file_path_to_string(path: tauri_plugin_dialog::FilePath) -> Option<String> {
    path.as_path().map(|path| path.to_string_lossy().to_string())
}
