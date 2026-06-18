import os

import operator_dashboard.app as app_module


def test_runtime_preflight_injects_msys2_gtk_path_when_missing(monkeypatch):
    gtk_path = r"C:\msys64\ucrt64\bin"

    # Simulate path exists but is not currently present in PATH.
    original_isdir = app_module.os.path.isdir
    monkeypatch.setattr(
        app_module.os.path,
        "isdir",
        lambda p: True if p == gtk_path else original_isdir(p),
    )
    monkeypatch.setenv("PATH", r"C:\Windows\System32")

    status = app_module._build_runtime_preflight_status("127.0.0.1:5050")

    assert status["msys_gtk_dll_path"]["path_exists"] is True
    assert status["msys_gtk_dll_path"]["in_process_path"] is True
    assert status["msys_gtk_dll_path"]["ready"] is True
    assert app_module._path_is_in_process_path(gtk_path) is True


def test_runtime_preflight_does_not_inject_when_gtk_path_missing(monkeypatch):
    gtk_path = r"C:\msys64\ucrt64\bin"

    # Simulate GTK path missing on disk.
    original_isdir = app_module.os.path.isdir
    monkeypatch.setattr(
        app_module.os.path,
        "isdir",
        lambda p: False if p == gtk_path else original_isdir(p),
    )
    monkeypatch.setenv("PATH", r"C:\Windows\System32")

    status = app_module._build_runtime_preflight_status("127.0.0.1:5050")

    assert status["msys_gtk_dll_path"]["path_exists"] is False
    assert status["msys_gtk_dll_path"]["in_process_path"] is False
    assert status["msys_gtk_dll_path"]["ready"] is False
    assert app_module._path_is_in_process_path(gtk_path) is False
