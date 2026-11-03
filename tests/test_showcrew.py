"""Small self-check for the showcrew command: python3 -m unittest tests.test_showcrew"""
import importlib.machinery, importlib.util, os, unittest

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "showcrew")
spec = importlib.util.spec_from_loader("showcrew", importlib.machinery.SourceFileLoader("showcrew", path))
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)


class T(unittest.TestCase):
    def test_secret_detection_never_needs_the_value(self):
        self.assertTrue(sc.have_secret("X", {"X": "abc"}))
        self.assertFalse(sc.have_secret("X", {"X": "  "}))
        self.assertFalse(sc.have_secret("X", {}))

    def test_every_core_domain_and_secret_has_an_explanation(self):
        self.assertTrue(all(why for _, _, why in sc.DOMAINS))
        self.assertTrue(all(len(s) == 4 and s[3] for s in sc.SECRETS))

    def test_unreachable_host_is_reported_blocked(self):
        self.assertFalse(sc.reachable("host.invalid", timeout=2))


if __name__ == "__main__":
    unittest.main()


class WordSync(unittest.TestCase):
    def test_anchor_and_missing(self):
        import importlib.util
        s = importlib.util.spec_from_file_location("ws", os.path.join(os.path.dirname(__file__), "..", "tools/wordsync/wordsync.py"))
        m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
        words = [{"word": "Start", "start": 0.4, "end": 0.7}, {"word": "free!", "start": 2.0, "end": 2.4}]
        r = m.wordsync(words, [{"id": "a", "word": "FREE", "offset": -0.1, "hold": 2}])
        self.assertEqual(r["a"], {"start": 1.9, "end": 3.9})
        with self.assertRaises(SystemExit):
            m.wordsync(words, [{"id": "b", "word": "nope"}])


class LipSync(unittest.TestCase):
    def test_in_sync_vs_shut(self):
        import subprocess, tempfile, numpy as np
        s = importlib.util.spec_from_file_location("ls", os.path.join(os.path.dirname(__file__), "..", "tools/lipsync/lipsync_check.py"))
        m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
        d = tempfile.mkdtemp(); fps, n = 12, 36
        t = np.arange(n) / fps
        talking = (t > 1) & (t < 2.2)
        frames = np.zeros((n, 64, 64), np.uint8)
        for i in range(n):
            frames[i, 40:44 + (10 if talking[i] and i % 2 else 0), 20:44] = 255
        sr = 16000; tt = np.arange(3 * sr) / sr
        tone = (np.sin(2 * np.pi * 220 * tt) * ((tt > 1) & (tt < 2.2)) * 20000).astype(np.int16)
        open(d + "/a.pcm", "wb").write(tone.tobytes())
        for name, shut in (("ok", False), ("shut", True)):
            fr = np.zeros_like(frames) if shut else frames
            fr[:, 10:20, 10:20] = 255
            p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "64x64", "-r", str(fps), "-i", "-",
                                  "-f", "s16le", "-ar", "16000", "-ac", "1", "-i", d + "/a.pcm", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                                  "-shortest", d + f"/{name}.mp4"], stdin=subprocess.PIPE)
            p.communicate(fr.tobytes())
        lines, corr, lag = m.analyse(*m.signals(d + "/ok.mp4", (0, 0, 64, 64), fps), fps)
        self.assertTrue(lines and lines[0][2] > 0.5 and abs(lag) <= 0.12, (lines, corr, lag))
        lines, _, _ = m.analyse(*m.signals(d + "/shut.mp4", (0, 0, 64, 64), fps), fps)
        self.assertTrue(lines and lines[0][2] < 0.3, lines)


class Workflow(unittest.TestCase):
    def test_resolve_word_and_overrun(self):
        s = importlib.util.spec_from_file_location("wf", os.path.join(os.path.dirname(__file__), "..", "tools/workflow/workflow.py"))
        m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
        import json, tempfile
        d = tempfile.mkdtemp(); json.dump([{"word": "free", "start": 2.0, "end": 2.4}], open(d + "/t.json", "w"))
        rows, dur, bad = m.resolve({"duration": 3, "transcript": "t.json", "items": [{"id": "a", "kind": "text", "at": {"word": "free"}, "hold": 2}]}, d)
        self.assertEqual((rows[0]["start"], dur), (2.0, 3))
        self.assertTrue(bad)
