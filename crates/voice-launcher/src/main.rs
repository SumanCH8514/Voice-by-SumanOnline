#![windows_subsystem = "windows"]

use std::env;
use std::os::windows::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::ptr::null;
use std::thread;
use std::time::Duration;

use windows_sys::Win32::Foundation::{CloseHandle, GetLastError, ERROR_ALREADY_EXISTS, HANDLE};
use windows_sys::Win32::System::Threading::CreateMutexW;
use windows_sys::Win32::UI::WindowsAndMessaging::{MessageBoxW, MB_ICONINFORMATION, MB_OK};

const CREATE_NO_WINDOW: u32 = 0x08000000;
const MUTEX_NAME: &str = "Global\\VoiceBySumanOnline_SingleInstanceMutex\0";

fn to_wide_chars(s: &str) -> Vec<u16> {
    s.encode_utf16().collect()
}

fn show_info(title: &str, msg: &str) {
    let t_wide = to_wide_chars(title);
    let m_wide = to_wide_chars(msg);
    unsafe {
        MessageBoxW(
            0,
            m_wide.as_ptr(),
            t_wide.as_ptr(),
            MB_OK | MB_ICONINFORMATION,
        );
    }
}

struct SingleInstanceGuard {
    handle: HANDLE,
}

impl SingleInstanceGuard {
    fn try_acquire() -> Result<Self, ()> {
        let name_wide = to_wide_chars(MUTEX_NAME);
        unsafe {
            let handle = CreateMutexW(null(), 1, name_wide.as_ptr());
            if handle == 0 {
                return Err(());
            }
            if GetLastError() == ERROR_ALREADY_EXISTS {
                CloseHandle(handle);
                return Err(());
            }
            Ok(SingleInstanceGuard { handle })
        }
    }
}

impl Drop for SingleInstanceGuard {
    fn drop(&mut self) {
        if self.handle != 0 {
            unsafe {
                CloseHandle(self.handle);
            }
        }
    }
}

fn find_project_root() -> PathBuf {
    if let Ok(exe_path) = env::current_exe() {
        if let Some(parent) = exe_path.parent() {
            if parent.join("voice_by_sumanonline").exists() {
                return parent.to_path_buf();
            }
            if let Some(grandparent) = parent.parent() {
                if grandparent.join("voice_by_sumanonline").exists() {
                    return grandparent.to_path_buf();
                }
                if let Some(g2) = grandparent.parent() {
                    if g2.join("voice_by_sumanonline").exists() {
                        return g2.to_path_buf();
                    }
                }
            }
        }
    }
    if let Ok(cwd) = env::current_dir() {
        if cwd.join("voice_by_sumanonline").exists() {
            return cwd;
        }
    }
    PathBuf::from(r"E:\Projects\SumanOnline Voice")
}

fn find_python_executable(root: &Path) -> Option<PathBuf> {
    let candidates = [
        root.join(".venv").join("Scripts").join("pythonw.exe"),
        root.join(".venv").join("Scripts").join("python.exe"),
        PathBuf::from("pythonw.exe"),
        PathBuf::from("python.exe"),
    ];

    for cand in candidates {
        if cand.is_file() {
            return Some(cand);
        }
    }
    Some(PathBuf::from("python.exe"))
}

fn spawn_engine(root: &Path, py_exe: &Path) -> std::io::Result<Child> {
    Command::new(py_exe)
        .arg("-m")
        .arg("voice_by_sumanonline.main")
        .current_dir(root)
        .creation_flags(CREATE_NO_WINDOW)
        .spawn()
}

fn open_studio_in_browser() {
    thread::sleep(Duration::from_millis(1200));
    let _ = Command::new("cmd")
        .args(["/C", "start", "http://localhost:48922"])
        .creation_flags(CREATE_NO_WINDOW)
        .spawn();
}

fn main() {
    let _guard = match SingleInstanceGuard::try_acquire() {
        Ok(g) => g,
        Err(_) => {
            show_info(
                "Voice by SumanOnline\0",
                "Voice by SumanOnline is already running in your system tray.\0",
            );
            open_studio_in_browser();
            return;
        }
    };

    let root = find_project_root();
    let py_exe = match find_python_executable(&root) {
        Some(p) => p,
        None => {
            show_info(
                "Error\0",
                "Could not locate Python environment. Please run installer first.\0",
            );
            return;
        }
    };

    let mut child = match spawn_engine(&root, &py_exe) {
        Ok(c) => c,
        Err(e) => {
            show_info(
                "Launch Error\0",
                &format!("Failed to start Voice by SumanOnline engine: {}\0", e),
            );
            return;
        }
    };

    let args: Vec<String> = env::args().collect();
    if args.iter().any(|a| a == "--ui") {
        thread::spawn(open_studio_in_browser);
    }

    let _ = child.wait();
}
