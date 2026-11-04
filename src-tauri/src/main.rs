// Prevents an extra console window on Windows in release builds.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use device_query::{DeviceQuery, DeviceState, Keycode};
use serde::Serialize;
use std::collections::HashSet;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;
use tauri::menu::{CheckMenuItem, Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::tray::TrayIconBuilder;
use tauri::{AppHandle, Emitter, Manager, PhysicalPosition, WebviewWindow};
use tauri_plugin_autostart::{MacosLauncher, ManagerExt};

const WIN_W: f64 = 200.0;
const WIN_H: f64 = 230.0;

/// Only the *kind* of key goes to the frontend, never which letter was typed.
#[derive(Clone, Serialize)]
struct KeyEvent {
    kind: &'static str, // "key" | "backspace" | "enter" | "save"
}

fn name(k: &Keycode) -> String {
    format!("{:?}", k) // e.g. "Backspace", "LControl", "LMeta" on every platform
}

fn is_modifier(n: &str) -> bool {
    ["Control", "Meta", "Command", "Shift", "Alt", "Option"].iter().any(|m| n.contains(m))
}

fn classify(n: &str, held: &HashSet<String>) -> &'static str {
    let ctrl_or_cmd = held.iter().any(|h| h.contains("Control") || h.contains("Meta") || h.contains("Command"));
    match n {
        "Backspace" | "Delete" => "backspace",
        "Enter" | "NumpadEnter" => "enter",
        "S" if ctrl_or_cmd => "save",
        _ => "key",
    }
}

fn spawn_keyboard_watcher(app: AppHandle, paused: Arc<AtomicBool>) {
    thread::spawn(move || {
        let device = DeviceState::new();
        let mut prev: HashSet<String> = HashSet::new();
        loop {
            let now: HashSet<String> = device.get_keys().iter().map(name).collect();
            if !paused.load(Ordering::Relaxed) {
                for k in now.difference(&prev) {
                    if !is_modifier(k) {
                        let _ = app.emit("pet-key", KeyEvent { kind: classify(k, &now) });
                    }
                }
            }
            prev = now;
            thread::sleep(Duration::from_millis(12));
        }
    });
}

/// Park the window in the bottom-right corner, above the taskbar/dock.
fn go_home(win: &WebviewWindow) {
    if let Ok(Some(mon)) = win.current_monitor() {
        let (size, pos, s) = (mon.size(), mon.position(), mon.scale_factor());
        let _ = win.set_position(PhysicalPosition::new(
            pos.x + size.width as i32 - (WIN_W * s) as i32 - (20.0 * s) as i32,
            pos.y + size.height as i32 - (WIN_H * s) as i32 - (70.0 * s) as i32,
        ));
    }
}

fn build_tray(app: &AppHandle, paused: Arc<AtomicBool>) -> tauri::Result<()> {
    let pause = CheckMenuItem::with_id(app, "pause", "暂停感知键盘", true, false, None::<&str>)?;
    let through = CheckMenuItem::with_id(app, "through", "鼠标穿透（不挡点击）", true, false, None::<&str>)?;
    let low = CheckMenuItem::with_id(app, "sens_low", "低：我本来就打字快", true, false, None::<&str>)?;
    let mid = CheckMenuItem::with_id(app, "sens_mid", "中：默认", true, true, None::<&str>)?;
    let high = CheckMenuItem::with_id(app, "sens_high", "高：一敲就慌", true, false, None::<&str>)?;
    let sens = Submenu::with_items(app, "灵敏度", true, &[&low, &mid, &high])?;
    let autostart_on = app.autolaunch().is_enabled().unwrap_or(false);
    let autostart = CheckMenuItem::with_id(app, "autostart", "开机自启", true, autostart_on, None::<&str>)?;
    let feed = MenuItem::with_id(app, "feed", "投喂小饼干 🍪", true, None::<&str>)?;
    let stats = MenuItem::with_id(app, "stats", "今日战绩", true, None::<&str>)?;
    let offwork = MenuItem::with_id(app, "offwork", "下班 / 回来上班", true, None::<&str>)?;
    let home = MenuItem::with_id(app, "home", "回到右下角", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
    let menu = Menu::with_items(
        app,
        &[
            &pause,
            &through,
            &sens,
            &autostart,
            &PredefinedMenuItem::separator(app)?,
            &feed,
            &stats,
            &offwork,
            &home,
            &PredefinedMenuItem::separator(app)?,
            &quit,
        ],
    )?;

    let (p, t) = (pause.clone(), through.clone());
    let (l, m, h) = (low.clone(), mid.clone(), high.clone());
    let a = autostart.clone();
    TrayIconBuilder::with_id("pet-tray")
        .icon(app.default_window_icon().cloned().expect("app icon missing"))
        .tooltip("打字恐慌桌宠")
        .menu(&menu)
        .on_menu_event(move |app, event| {
            let win = app.get_webview_window("main");
            match event.id().as_ref() {
                "pause" => {
                    let on = p.is_checked().unwrap_or(false);
                    paused.store(on, Ordering::Relaxed);
                    let _ = app.emit("pet-paused", on);
                }
                "through" => {
                    let on = t.is_checked().unwrap_or(false);
                    if let Some(w) = &win {
                        let _ = w.set_ignore_cursor_events(on);
                    }
                }
                id @ ("sens_low" | "sens_mid" | "sens_high") => {
                    // behave like radio buttons
                    let _ = l.set_checked(id == "sens_low");
                    let _ = m.set_checked(id == "sens_mid");
                    let _ = h.set_checked(id == "sens_high");
                    let _ = app.emit("pet-sensitivity", id.trim_start_matches("sens_"));
                }
                "autostart" => {
                    let want = a.is_checked().unwrap_or(false);
                    let mgr = app.autolaunch();
                    let res = if want { mgr.enable() } else { mgr.disable() };
                    if res.is_err() {
                        // roll the checkbox back so it never lies
                        let _ = a.set_checked(mgr.is_enabled().unwrap_or(false));
                    }
                }
                "feed" => {
                    let _ = app.emit("pet-feed", ());
                }
                "stats" => {
                    let _ = app.emit("pet-stats", ());
                }
                "offwork" => {
                    let _ = app.emit("pet-offwork", ());
                }
                "home" => {
                    if let Some(w) = &win {
                        go_home(w);
                        let _ = w.show();
                    }
                }
                "quit" => app.exit(0),
                _ => {}
            }
        })
        .build(app)?;
    Ok(())
}

fn main() {
    tauri::Builder::default()
        // A second launch (e.g. autostart + manual) just brings the pet back instead of a twin.
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(w) = app.get_webview_window("main") {
                let _ = w.show();
                go_home(&w);
            }
        }))
        .plugin(tauri_plugin_autostart::init(MacosLauncher::LaunchAgent, None))
        .setup(|app| {
            let paused = Arc::new(AtomicBool::new(false));
            if let Some(win) = app.get_webview_window("main") {
                go_home(&win);
            }
            build_tray(app.handle(), paused.clone())?;
            spawn_keyboard_watcher(app.handle().clone(), paused);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Typing Panic Pet");
}
