"""Compile flex-eq and run real PCM through it (fifo in -> fifo out)."""
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
SRC = Path(__file__).resolve().parents[1] / "spotify_flex" / "eq" / "flexeq.c"
RATE = 44100
LA = 256  # limiter look-ahead (frames): output is the input delayed by this much


@pytest.fixture(scope="module")
def binary(tmp_path_factory):
    if not shutil.which("gcc"):
        pytest.skip("gcc missing")
    out = tmp_path_factory.mktemp("eq") / "flex-eq"
    subprocess.run(["gcc", "-O2", "-Wall", "-Werror", "-o", str(out), str(SRC), "-lm"], check=True)
    return out


def tone(freq, seconds=1.0, amp=0.25):
    t = np.arange(int(RATE * seconds)) / RATE
    mono = (np.sin(2 * np.pi * freq * t) * amp * 32767).astype(np.int16)
    return np.repeat(mono, 2)  # interleaved stereo


def run(binary, tmp_path, pcm, control, change=None):
    fin, fout, ctl = tmp_path / "in", tmp_path / "out", tmp_path / "eq.conf"
    for f in (fin, fout):
        if f.exists():
            f.unlink()
        os.mkfifo(f)
    ctl.write_text(control)
    proc = subprocess.Popen([str(binary), str(fin), str(fout), str(ctl)], stderr=subprocess.PIPE)
    got = bytearray()

    def reader():
        with open(fout, "rb") as fh:
            while chunk := fh.read(65536):
                got.extend(chunk)

    th = threading.Thread(target=reader)
    th.start()
    data = pcm.tobytes()
    with open(fin, "wb") as fh:
        half = len(data) // 2 // 4 * 4
        fh.write(data[:half])
        if change:
            fh.flush()
            time.sleep(0.3)
            ctl.write_text(change)
            time.sleep(0.3)
        fh.write(data[half:])
    time.sleep(0.5)
    proc.terminate()
    proc.wait(5)
    th.join(5)
    return np.frombuffer(bytes(got), dtype=np.int16)


def level(x):
    return 20 * np.log10(np.sqrt(np.mean((x.astype(float) / 32768) ** 2)) + 1e-12)


def test_flat_is_bit_exact(binary, tmp_path):
    pcm = tone(1000) + tone(60, amp=0.1)
    pcm[:200] = 32767  # even full-scale input passes untouched when the EQ is flat/off
    for conf in ("1 0 0 0 0 0 0\n", "0 6 6 6 6 6 6\n"):
        out = run(binary, tmp_path, pcm, conf)
        assert len(out) == len(pcm) + LA * 2
        assert not out[: LA * 2].any() and np.array_equal(out[LA * 2:], pcm)


def test_bands(binary, tmp_path):
    ref = {f: level(tone(f)) for f in (60, 1000, 15000)}
    conf = "1 6 0 0 0 0 -6\n"  # curve peak ~6 dB -> no overall reduction any more
    for f, expect in ((60, 6), (1000, 0), (15000, -6)):
        out = run(binary, tmp_path, tone(f), conf)
        settled = out[len(out) // 2:]
        assert abs(level(settled) - ref[f] - expect) < 1.0, (f, level(settled) - ref[f])


def test_live_change_and_no_clipping(binary, tmp_path):
    pcm = tone(15000, seconds=2.0, amp=0.2)
    out = run(binary, tmp_path, pcm, "1 0 0 0 0 0 0\n", change="1 0 0 0 0 0 -12\n")
    assert len(out) == len(pcm) + LA * 2
    first, last = out[: len(out) // 4], out[-len(out) // 4:]
    assert level(last) < level(first) - 9  # treble cut arrived without restarting
    loud = run(binary, tmp_path, tone(60, amp=0.95), "1 12 12 0 0 0 0\n")
    peak = np.abs(loud.astype(int))
    assert peak.max() <= 31500  # look-ahead limiter keeps peaks at -0.5 dBFS, no clipping
    assert np.mean(peak >= 31000) < 0.02


def test_bass_boost_keeps_voice_level(binary, tmp_path):
    """Bass-Booster must not make mids (voices) noticeably quieter."""
    ref = level(tone(1000))
    out = run(binary, tmp_path, tone(1000), "1 6 4 1 0 0 0\n")
    assert level(out[len(out) // 2:]) - ref > -1.0
