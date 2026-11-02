"""Output isolation regressions, separate from the retained scientific census."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import reproduce


class OutputDirectoryTests(unittest.TestCase):
    def test_reserves_new_external_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'new-run'
            self.assertEqual(reproduce.reserve_output_directory(target), target.resolve())
            self.assertTrue(target.is_dir())
            self.assertEqual(list(target.iterdir()), [])

    def test_existing_output_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            marker = target / 'execution.json'
            marker.write_text('retained timing', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                reproduce.reserve_output_directory(target)
            self.assertEqual(marker.read_text(encoding='utf-8'), 'retained timing')
            self.assertEqual(list(target.iterdir()), [marker])

    def test_rejects_repository_root_and_descendant(self):
        for path in [ROOT, ROOT / 'results', ROOT / 'new-run-not-created']:
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'outside'):
                reproduce.reserve_output_directory(path)
        self.assertFalse((ROOT / 'new-run-not-created').exists())

    def test_missing_output_stops_before_generation(self):
        with patch.object(sys, 'argv', ['reproduce.py']), patch.object(reproduce, 'generate') as generate:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failure:
                reproduce.main()
            self.assertEqual(failure.exception.code, 2)
            generate.assert_not_called()

    def test_existing_output_cli_stops_before_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sys, 'argv', ['reproduce.py', '--output', directory]), patch.object(reproduce, 'generate') as generate:
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failure:
                    reproduce.main()
                self.assertEqual(failure.exception.code, 2)
                generate.assert_not_called()

    def test_rejects_symbolic_link_and_dangling_link(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for index, target in enumerate([ROOT, base / 'missing-target']):
                link = base / ('alias-' + str(index))
                try:
                    link.symlink_to(target, target_is_directory=True)
                except (OSError, NotImplementedError):
                    self.skipTest('Host does not allow directory symbolic links')
                with self.subTest(target=target), self.assertRaises(ValueError):
                    reproduce.reserve_output_directory(link)
                if index == 1:
                    self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
