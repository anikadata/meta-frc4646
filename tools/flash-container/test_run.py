"""Prevent a zero-exit upstream device failure from looking like a good flash.

All Docker calls are replaced by a fixture; this never accesses hardware.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class FlashResultTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.flash = self.root / 'flash'
        self.flash.mkdir()
        (self.flash / '.env.initrd-flash').touch()
        (self.flash / 'initrd-flash').touch(mode=0o755)
        docker = self.root / 'docker'
        docker.write_text('#!/bin/sh\n'
                          '[ "$1" = build ] && exit 0\n'
                          'printf "%s\\n" "$FIXTURE_FLASH_OUTPUT"\n'
                          'exit "$FIXTURE_FLASH_EXIT"\n')
        docker.chmod(0o755)

    def run_flash(self, output, exit_code=0, *args):
        return subprocess.run([
            str(Path(__file__).with_name('run')), str(self.flash), *args,
        ], capture_output=True, text=True, env={
            **os.environ, 'PATH': str(self.root) + ':' + os.environ['PATH'],
            'FIXTURE_FLASH_OUTPUT': output, 'FIXTURE_FLASH_EXIT': str(exit_code),
        })

    def test_explicit_device_success(self):
        self.assertEqual(self.run_flash('Final status: SUCCESS').returncode, 0)

    def test_all_device_statuses_successful(self):
        self.assertEqual(self.run_flash(
            'Final status: SUCCESS\nFinal status: SUCCESS').returncode, 0)

    def test_zero_exit_device_failure(self):
        result = self.run_flash('Final status: FAILED')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('did not report device SUCCESS', result.stderr)

    def test_missing_device_status(self):
        self.assertNotEqual(self.run_flash('Flash host finished').returncode, 0)

    def test_success_does_not_hide_another_device_failure(self):
        for lines in (
            ['Final status: SUCCESS', 'Final status: FAILED'],
            ['Final status: FAILED', 'Final status: SUCCESS'],
        ):
            with self.subTest(lines=lines):
                self.assertNotEqual(self.run_flash('\n'.join(lines)).returncode, 0)

    def test_unknown_final_status_is_not_success(self):
        self.assertNotEqual(self.run_flash(
            'Final status: SUCCESS\nFinal status: UNKNOWN').returncode, 0)

    def test_host_error_even_with_success_text(self):
        self.assertEqual(self.run_flash('Final status: SUCCESS', 7).returncode, 7)

    def test_help_needs_no_device_status(self):
        self.assertEqual(self.run_flash('Usage:', 0, '--help').returncode, 0)


if __name__ == '__main__':
    unittest.main()
