// Prevents an extra console window on Windows in release builds.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use device_query::{DeviceQuery, DeviceState, Keycode};
use serde::Serialize;
use std::collections::HashSet;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use tauri::menu::{CheckMenuItem, Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::tray::TrayIconBuilder;
use tauri::{AppHandle, Emitter, Manager, PhysicalPosition, State, WebviewWindow};
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

// ---- v0.6: keyboard permission (macOS needs Accessibility for global key state) ----
#[cfg(target_os = "macos")]
#[link(name = "ApplicationServices", kind = "framework")]
extern "C" {
    fn AXIsProcessTrusted() -> u8;
}

fn has_keyboard_permission() -> bool {
    #[cfg(target_os = "macos")]
    {
        unsafe { AXIsProcessTrusted() != 0 }
    }
    #[cfg(not(target_os = "macos"))]
    {
        true
    }
}

#[tauri::command]
fn keyboard_permission() -> bool {
    has_keyboard_permission()
}

#[tauri::command]
fn open_permission_settings() {
    #[cfg(target_os = "macos")]
    {
        let _ = std::process::Command::new("open")
            .arg("x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")
            .spawn();
    }
}

// ---- v0.6: click-through everywhere except on the pet itself ----
/// The pet's body as an ellipse, in CSS pixels relative to the window (rx = 0: hidden).
#[derive(Clone, Copy, Default)]
struct Hitbox {
    cx: f64,
    cy: f64,
    rx: f64,
    ry: f64,
}

struct HitState {
    box_: Mutex<Hitbox>,
    force_through: AtomicBool,
}

#[tauri::command]
fn set_hitbox(state: State<'_, Arc<HitState>>, cx: f64, cy: f64, rx: f64, ry: f64) {
    if let Ok(mut b) = state.box_.lock() {
        *b = Hitbox { cx, cy, rx, ry };
    }
}

fn spawn_hit_tester(app: AppHandle, hit: Arc<HitState>) {
    thread::spawn(move || {
        let mut ignoring: Option<bool> = None;
        loop {
            thread::sleep(Duration::from_millis(40));
            let Some(win) = app.get_webview_window("main") else { continue };
            let b = hit.box_.lock().map(|b| *b).unwrap_or_default();
            let inside = match (win.cursor_position(), win.outer_position(), win.scale_factor()) {
                (Ok(c), Ok(p), Ok(s)) if b.rx > 0.0 && b.ry > 0.0 => {
                    let x = (c.x - p.x as f64) / s - b.cx;
                    let y = (c.y - p.y as f64) / s - b.cy;
                    (x / b.rx).powi(2) + (y / b.ry).powi(2) <= 1.0
                }
                _ => false,
            };
            let want = hit.force_through.load(Ordering::Relaxed) || !inside;
            if ignoring != Some(want) {
                if win.set_ignore_cursor_events(want).is_ok() {
                    ignoring = Some(want);
                }
            }
        }
    });
}

fn spawn_keyboard_watcher(app: AppHandle, paused: Arc<AtomicBool>) {
    thread::spawn(move || {
        // On macOS DeviceState::new() panics without the Accessibility permission (and with
        // panic = "abort" that would take the whole app down), so wait for it first.
        while !has_keyboard_permission() {
            thread::sleep(Duration::from_secs(2));
        }
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

fn build_tray(app: &AppHandle, paused: Arc<AtomicBool>, hit: Arc<HitState>) -> tauri::Result<()> {
    let pause = CheckMenuItem::with_id(app, "pause", "暂停感知键盘", true, false, None::<&str>)?;
    let through = CheckMenuItem::with_id(app, "through", "完全穿透（摸不到团子）", true, false, None::<&str>)?;
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
                    // the hit tester applies it on its next pass
                    hit.force_through.store(t.is_checked().unwrap_or(false), Ordering::Relaxed);
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
        .invoke_handler(tauri::generate_handler![set_hitbox, keyboard_permission, open_permission_settings])
        .setup(|app| {
            let paused = Arc::new(AtomicBool::new(false));
            let hit = Arc::new(HitState { box_: Mutex::new(Hitbox::default()), force_through: AtomicBool::new(false) });
            app.manage(hit.clone());
            if let Some(win) = app.get_webview_window("main") {
                go_home(&win);
            }
            build_tray(app.handle(), paused.clone(), hit.clone())?;
            spawn_keyboard_watcher(app.handle().clone(), paused);
            spawn_hit_tester(app.handle().clone(), hit);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Typing Panic Pet");
}
