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
