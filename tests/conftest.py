import pytest


@pytest.fixture(autouse=True)
def clear_private_gui_sessions():
    from core.private_panels import PANELS, LOCKS
    PANELS.clear()
    LOCKS.clear()
    yield
    for panel in PANELS.values():
        if panel.view is not None:
            panel.view.stop()
    PANELS.clear()
    LOCKS.clear()
