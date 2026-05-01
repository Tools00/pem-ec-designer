# UI Launch Notes — PySide6 + pyvistaqt + macOS arm64

Findings aus dem Smoke-Test (`scripts/smoke_pyvistaqt.py`, 2026-05-01).
Diese Punkte werden im UI-Code sonst wieder zur Stunden-Fresser-Falle.

## 1. Qt-Plugin-Pfad explizit setzen (Anaconda-Python)

Mit System-/conda-Python findet PySide6 seine `platforms`-Plugins nicht
automatisch:

```
qt.qpa.plugin: Could not find the Qt platform plugin "cocoa" in ""
```

**Fix:** `QT_PLUGIN_PATH` setzen, bevor `QApplication` erstellt wird.

```python
import os, PySide6
os.environ["QT_PLUGIN_PATH"] = str(
    Path(PySide6.__file__).parent / "Qt" / "plugins"
)
```

Im UI-Entry-Point (`__main__.py`) ganz oben einsetzen — vor jedem
PySide6-Import außer PySide6 selbst.

## 2. `offscreen`-Platform crasht (SIGSEGV) auf macOS arm64

`QT_QPA_PLATFORM=offscreen` führt zu Segfault sobald `QtInteractor`
einen Render-Context anfordert. **Nicht verwenden.** Headless-Tests
für UI-Code laufen nur mit `cocoa` und sichtbarem (oder via
`window.hide()` versteckten) Fenster, oder gar nicht.

CI-Konsequenz: UI-Tests bleiben **lokal**, nicht in GitHub-Actions
(Linux-Runner). Geometrie/Schema/Physik bleiben UI-frei und CI-getestet.

## 3. Screenshot braucht echten Render-Context

`plotter.screenshot()` ohne vorheriges `win.show()` + `plotter.render()`
wirft `RenderWindowUnavailable: Render window is not current.`

**Reihenfolge:**

```python
win.show()
app.processEvents()
plotter.render()
app.processEvents()
plotter.screenshot(path)
```

## Smoke-Test-Aufruf (für Wiederholung)

```bash
QT_PLUGIN_PATH=$(python -c "import PySide6, os; print(os.path.join(os.path.dirname(PySide6.__file__), 'Qt', 'plugins'))") \
  PYTHONPATH=src python scripts/smoke_pyvistaqt.py
```

Erwartung: Exit 0, PNG > 1000 Bytes in `$TMPDIR/pem_ec_designer_smoke.png`.
