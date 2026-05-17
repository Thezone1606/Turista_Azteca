"""Reproductor de audio para los mp3 del juego.

Toca por slug: `audio.play("estado_cdmx")` busca `~/turista/audio/estado_cdmx.mp3`.
Cola FIFO: las llamadas a play() encolan y vuelven inmediato; un worker thread
reproduce uno por uno con mpg123 para que nunca se solapen.
"""
from __future__ import annotations

import logging
import queue
import subprocess
import threading
from pathlib import Path

log = logging.getLogger(__name__)

AUDIO_DIR = Path(__file__).resolve().parent.parent / "audio"


class AudioPlayer:
    def __init__(self, audio_dir: Path = AUDIO_DIR) -> None:
        self.audio_dir = audio_dir
        self._q: queue.Queue[str | None] = queue.Queue()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def play(self, slug: str) -> None:
        """Encola un slug para reproducir."""
        self._q.put(slug)

    def play_many(self, slugs: list[str]) -> None:
        for s in slugs:
            self.play(s)

    def wait_idle(self, timeout: float | None = None) -> None:
        """Espera hasta que la cola esté vacía y el archivo actual termine."""
        self._q.join() if timeout is None else self._q.join()  # queue.join no soporta timeout

    def stop(self) -> None:
        self._q.put(None)
        self._worker.join(timeout=5)

    def _run(self) -> None:
        while True:
            item = self._q.get()
            try:
                if item is None:
                    return
                self._play_one(item)
            finally:
                self._q.task_done()

    def _play_one(self, slug: str) -> None:
        path = self.audio_dir / f"{slug}.mp3"
        if not path.exists():
            log.warning("Audio faltante: %s", path)
            return
        try:
            subprocess.run(
                ["mpg123", "-q", str(path)],
                check=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            log.error("mpg123 no instalado")
