import operator_dashboard.app as app_module


def test_windows_gtk_dll_directory_loader_invokes_add_dll_directory(monkeypatch):
    gtk_path = r"C:\msys64\ucrt64\bin"
    calls = []
    original_isdir = app_module.os.path.isdir

    class DummyHandle:
        pass

    monkeypatch.setattr(app_module.os, "name", "nt", raising=False)
    monkeypatch.setattr(app_module.os.path, "isdir", lambda p: True if p == gtk_path else original_isdir(p))
    monkeypatch.setattr(app_module.os, "add_dll_directory", lambda p: calls.append(p) or DummyHandle(), raising=False)
    monkeypatch.setattr(app_module, "_BUTTON2_GTK_DLL_DIR_HANDLE", None)

    loaded = app_module._ensure_windows_gtk_dll_directory_loaded(gtk_path)

    assert loaded is True
    assert calls == [gtk_path]
    assert app_module._BUTTON2_GTK_DLL_DIR_HANDLE is not None


def test_runtime_preflight_calls_windows_dll_loader_before_weasyprint_import(monkeypatch):
    gtk_path = r"C:\msys64\ucrt64\bin"
    state = {"called": False}
    original_isdir = app_module.os.path.isdir

    monkeypatch.setattr(app_module.os.path, "isdir", lambda p: True if p == gtk_path else original_isdir(p))

    def _fake_loader(path):
        if path == gtk_path:
            state["called"] = True
            return True
        return False

    monkeypatch.setattr(app_module, "_ensure_windows_gtk_dll_directory_loaded", _fake_loader)

    status = app_module._build_runtime_preflight_status("127.0.0.1:5050")

    assert state["called"] is True
    assert "weasyprint_render_readiness" in status
