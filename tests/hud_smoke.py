from __future__ import annotations

import logging
import sys
import threading
import time

from voice_by_sumanonline.audio import Recorder
from voice_by_sumanonline.hud import HUD
from voice_by_sumanonline.preview import StreamingPreview

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    rec = Recorder()
    preview_partials: list[str] = []

    def on_partial(text: str) -> None:
        preview_partials.append(text)

    preview = StreamingPreview(on_partial=on_partial)
    hud = HUD()

    t0 = time.monotonic()
    while not preview.is_ready() and time.monotonic() - t0 < 5.0:
        time.sleep(0.05)
    preview_ready = preview.is_ready()
    print(f"Preview ready: {preview_ready}")

    def driver() -> None:
        time.sleep(0.3)
        hud.show_recording(preview_active=preview_ready)
        time.sleep(0.5)

        if preview_ready:
            hud.set_preview_text("hello world")
            time.sleep(0.3)
            hud.set_preview_text("hello world this is a much longer transcript")
            time.sleep(0.4)

        hud.show_processing()
        time.sleep(0.4)

        hud.hide()
        time.sleep(0.25)

        hud.close()

    threading.Thread(target=driver, daemon=True).start()
    hud.run()
    print("OK: HUD event loop exited cleanly.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
