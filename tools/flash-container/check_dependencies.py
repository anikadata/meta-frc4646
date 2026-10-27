"""Check the extracted T234 archive's host helpers without accessing USB."""
from pathlib import Path
import shutil
import struct
import subprocess
import sys

for program in ('dtc', 'xmllint', 'bmaptool', 'cpio', 'sgdisk', 'parted',
                'mount', 'umount', 'mkfs.vfat', 'openssl'):
    if not shutil.which(program):
        raise SystemExit(f'Missing flash host command: {program}')

# Import the real NVIDIA helpers to catch their Python dependencies before
# the privileged container gets access to a recovery device.
sys.path.insert(0, '/flash')
import tegraflash_internal
import tegraflash_impl_t234
import tegrasign_v3

checked = set()
for path in Path('/flash').iterdir():
    if not path.is_file() or not path.stat().st_mode & 0o111:
        continue
    with path.open('rb') as stream:
        header = stream.read(20)
    if (len(header) < 20 or header[:4] != b'\x7fELF'
            or struct.unpack('<H', header[18:20])[0] not in (3, 62)):
        continue
    result = subprocess.run(['ldd', str(path)], capture_output=True, text=True)
    output = result.stdout + result.stderr
    if ('not found' in output or (result.returncode and
            'not a dynamic executable' not in output and 'statically linked' not in output)):
        raise SystemExit(f'Unresolved flash host binary {path}:\n{output}')
    checked.add(path.name)

required = {'tegrarcm_v2', 'tegrahost_v2', 'tegrabct_v2', 'tegraparser_v2',
            'tegraopenssl', 'chkbdinfo'}
if required - checked:
    raise SystemExit(f'Missing x86 flash helpers: {sorted(required - checked)}')
print(f'Flash prerequisites passed: NVIDIA Python imports and {len(checked)} x86 helpers.')
