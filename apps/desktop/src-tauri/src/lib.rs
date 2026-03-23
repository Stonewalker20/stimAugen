mod commands;
mod paths;
mod sidecar;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let runtime_paths = paths::resolve_runtime_paths(app)?;
            paths::ensure_runtime_directories(&runtime_paths)?;
            app.manage(sidecar::HostState::new(runtime_paths));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_app_paths,
            commands::pick_audio_file,
            commands::pick_audio_files,
            commands::save_export_file,
            commands::confirm_voice_cloning,
            commands::ensure_sidecar_running,
            commands::sidecar_health,
            commands::call_sidecar_route
        ])
        .run(tauri::generate_context!())
        .expect("error while running Home Voice Studio");
}
