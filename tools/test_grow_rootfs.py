"""Check rootfs grow dispatch without touching any disk or filesystem."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = (Path(__file__).resolve().parents[1] /
          'layers/meta-tegrademo/recipes-aos/configuration/aos-configuration/'
          'contents/usr/sbin/aos-grow-rootfs')


class GrowRootfsTest(unittest.TestCase):
    def run_grow(self, filesystem, failure=0):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commands = {
                'findmnt': '#!/bin/sh\ncase "$*" in\n'
                           ' *FSTYPE*) echo "$TEST_FS";;\n'
                           ' *SOURCE*) echo /dev/nvme0n1p1;;\nesac\n',
                'xfs_growfs': '#!/bin/sh\necho "xfs_growfs $*"\nexit "$TEST_RC"\n',
                'resize2fs': '#!/bin/sh\necho "resize2fs $*"\nexit "$TEST_RC"\n',
            }
            for name, content in commands.items():
                path = root / name
                path.write_text(content)
                path.chmod(0o755)
            return subprocess.run(
                ['sh', str(SCRIPT)], capture_output=True, text=True,
                env=dict(os.environ, PATH=f'{root}:/usr/bin:/bin',
                         TEST_FS=filesystem, TEST_RC=str(failure)))

    def test_ext4_uses_block_device(self):
        result = self.run_grow('ext4')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'resize2fs /dev/nvme0n1p1')

    def test_xfs_uses_mountpoint(self):
        result = self.run_grow('xfs')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'xfs_growfs /')

    def test_unknown_filesystem_is_not_modified(self):
        result = self.run_grow('overlay')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')

    def test_resize_failure_propagates(self):
        self.assertEqual(self.run_grow('ext4', failure=7).returncode, 7)


if __name__ == '__main__':
    unittest.main()
