# tegra-demo-distro

Reference/demo distribution for NVIDIA Jetson platforms
using Yocto Project tools and the [meta-tegra](https://github.com/OE4T/meta-tegra) BSP layer.

Metadata layers are brought in as git submodules:

| Layer Repo            | Branch         | Description                                         |
| --------------------- | ---------------|---------------------------------------------------- |
| openembedded-core     | wrynose        | OE-Core                                             |
| bitbake               | 2.18           | BitBake                                             |
| meta-tegra            | wrynose        | Pinned L4T R39.2.0 / JetPack 7.2                     |
| meta-tegra-community  | wrynose        | OE4T layer with additions from the community        |
| meta-openembedded     | wrynose        | OpenEmbedded layers                                 |
| meta-virtualization   | wrynose        | Virtualization layer                                |

Use the recorded submodule commits, not the moving branch tips:

```
git submodule update --init --recursive
```

## Usage

This checkout targets the confirmed NVIDIA developer kit: an Orin Nano 8GB
P3767-0003 module on a P3768 carrier. Use `p3768-0000-p3767-0003` for this
hardware. The generic `jetson-orin-nano-devkit` machine defaults to SKU 0005;
it is not the machine for the connected SKU 0003 module. Confirm the module
and carrier before choosing a machine for another board, including a Seeed J401.
Build on Linux with a case-sensitive build filesystem. To build, run:

```
export MACHINE=p3768-0000-p3767-0003
. layers/oe-init-build-env build
bitbake demo-image-base
```

The output directory is `build/tmp/deploy/images/p3768-0000-p3767-0003/`.
The flash archive uses the `.tegraflash-tar.zst` suffix and contains an ext4
root filesystem. The installed growth service supports both ext4 and XFS;
XFS conversion is optional and is not part of the build above.

### Isolated Linux build environment

`tools/build-container/run` builds a Debian 13 tools container and runs commands
as your host UID/GID. It requires access to a running Docker daemon. Initialize
the pinned submodules first, then select the machine for the actual module and
carrier (the example below is specifically P3767-0003 on P3768):

```sh
git submodule update --init --recursive
tools/build-container/run bash -lc '
  export MACHINE=p3768-0000-p3767-0003
  . layers/oe-init-build-env build
  bitbake demo-image-base
'
```

The parent workspace is bind-mounted at its original path. Downloads, shared
state, and build output remain in `build/` across container runs. The launcher
allows BitBake's task namespaces inside the container without changing host
AppArmor settings. This builds the image only; XFS conversion, sysroot export,
and flashing are separate steps with their own mount/device requirements.

The local build on the 38 GiB Linux host uses `BB_NUMBER_THREADS = "6"` and
`PARALLEL_MAKE = "-j6"` in the ignored `build/conf/auto.conf`. Keep those limits
on this host when reproducing the build.

To flash, extract the archive, then run `sudo ./initrd-flash` with the Orin in
recovery mode and connected over USB. Flashing replaces the target system;
building the archive does not flash the connected device.

### Clean rebuild and containerized flash

A fresh recursive clone supplies all pinned layers. For a build that does not
reuse previously compiled shared state, start with empty `build/tmp` and
`build/sstate-cache` directories and set `SSTATE_MIRRORS = ""` in
`build/conf/auto.conf`. Downloaded source archives may be reused; their checksums
remain enforced. `INHERIT += "rm_work"` can reduce intermediate disk usage.
Do not remove another running build's directories.

On an x86-64 Linux host with Docker access, the flash container supplies Ubuntu 24.04
and the flashing tools without needing host package installation or host sudo:

```sh
mkdir -p /path/to/new-flash-directory
tar --zstd -xf /path/to/image.tegraflash-tar.zst -C /path/to/new-flash-directory
# With the intended Orin connected by USB-C and already in recovery mode:
tools/flash-container/run /path/to/new-flash-directory --usb-instance 3-3
```

Replace `3-3` with the actual USB bus/port path. The container uses privileged
device/mount access because Orin recovery exports USB mass-storage devices;
it has no network access. Only use a trusted flash archive and keep the device
powered throughout. The script writes boot firmware and the NVMe rootfs.
Back up target application/configuration files before flashing.
Before accessing USB, the wrapper checks the archive's actual NVIDIA Python
imports and x86 helper libraries in an unprivileged container.

Run the wrapper as your normal Docker-enabled user. In a GNOME session it
temporarily disables that user's media automount and restores both settings
on exit, including failures. On other desktops, disable their removable-media
automount for the flash; a host desktop mount is invisible to the container.
Avoid another logged-in desktop session automounting the same device.

For a running NVIDIA developer kit, NVIDIA documents
`sudo reboot --force forced-recovery` as the
[software recovery entry command](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/howto.html#force-recovery-mode).
Check `lsusb` for NVIDIA APX before flashing. Normal SSH/Ethernet access is
unavailable in recovery mode. The wrapper records a log in the extracted
directory and requires `Final status: SUCCESS`, because the upstream helper
can return zero even when its final device status is `FAILED`. Every reported
final status must succeed; one success cannot hide another failure. Confirm
booted-image identity, filesystem growth, and application tests afterward;
a completed image build alone is insufficient.

### Validated rebuild (2026-10-27)

The initial clean `demo-image-base` build completed all 12,260 tasks with zero
reused tasks. An actual SCTP listener test then exposed a missing runtime
crypto module: `sctp` loaded, but its default MD5 cookie authentication failed.
The corrected package group installs `kernel-module-md5`. Reassembling the
image from the freshly compiled packages executed 30 tasks and passed image QA.

Final image source: `71ff641ca882e45d9fa991f388fb465ec02f90fb` and the pinned submodules.
Final flash archive SHA256:

```text
0c21e23e35044ffaf7cc9febf3965a4d02e645c589f4b90d86eaebc73eb300e3
```

This image was flashed to the P3767-0003/P3768 developer kit with explicit
device `SUCCESS`. Booted system-file hashes, filesystem UUID, and SDK package
versions matched. The ext4 filesystem grew to about 872 GiB, all six CPU cores
came online in MAXN_SUPER, and CUDA samples and SCTP data exchange passed.

The paired software branch uses SDK revision `2026.10.27.1`, exported from this
exact image. A fresh GitHub clone downloaded it and completed 7,175 clean build
actions. The 68-file deployment passed loader checks, all 19 GPU and 19 NEON
recorded-image cases, four-channel stress and malformed-JPEG recovery,
supervised startup, Ethernet Foxglove/NetworkTables, and reboot validation.
No physical cameras or roboRIO were attached; capture, bandwidth, calibration,
and real robot integration still require those devices.

Image/SDK assets, test evidence, and the report are in the private software
repository's [validated release](https://github.com/team1868/software/releases/tag/wrynose-orin-2026.10.27.1).
Its `tools/wrynose_sysroot/README.md` documents setup on another Linux machine.
The October 27 diagnostic draft without the MD5 package was superseded.

To view the serial console:
```
python3 /usr/lib/python3/dist-packages/serial/tools/miniterm.py /dev/ttyUSB0 115200
```

# AOS compatibility before flashing

This image pins CUDA 13.2 and OpenCV 4.13. The paired software branch
`team1868/software:anikadata/newsysrootwrynose` selects a matching
Wrynose export instead of Walnascar (CUDA 12.6 / OpenCV 4.11). Install that
sysroot and rebuild the AOS bundle; see `tools/wrynose_sysroot/README.md`
and `2026/vision/README.md` in the software repository. Missing
`libcudart.so.12` or `libopencv_*.so.411` on the Orin indicates old binaries;
reflashing alone does not fix them.

The software branch's `tools/build_orin` installs its checksum-pinned sysroot
from that private repository's release assets and builds the correct
`//2026/vision:download` target. A Git checkout does not itself contain the large
headers/libraries archive. The software repository also includes an unprivileged
Ubuntu container exporter for this image's ext4 rootfs; see
`tools/export_wrynose_sysroot.py`. Regenerate and publish matching sysroot
metadata/assets when changing target runtime libraries.

The supplied September 23 image still contains the old camera naming rules
and no SCTP kernel module. Rebuild this layer's image before flashing so it
includes the reviewed camera, UVC, and SCTP fixes. An exported application
sysroot does not update those parts of an existing flash archive.

The UVC aliases below cover two alternative four-port hub layouts. Use one
layout at a time and verify `/dev/videoa` through `/dev/videod` against the
physical camera calibrations. Unknown USB layouts intentionally get no alias;
capture-device enumeration order is not a stable calibration identifier.

# UVC camera debugging

To turn on all debugging in dmesg:

```
echo 0xffff | sudo tee /sys/module/uvcvideo/parameters/trace
```

Set it back to 0 to turn it off.

```
echo 0 | sudo tee /sys/module/uvcvideo/parameters/trace
```

After stopping camera applications, reload UVC with the default full bandwidth:

```
sudo modprobe -r uvcvideo
sudo modprobe uvcvideo quirks=128 bandwidth_quirk_divisor=1
```

`dmesg` will spit out frame statistics, including bandwidth usage.

The image's `uvc.conf` sets these parameters. The October 27 image used divisor
16, which stalled the physical SPCA2630 camera after it negotiated 1600x1304
MJPEG at 60 fps. A controlled comparison reproduced zero frames with divisor
16 and continuous capture with divisor 1, followed by live AOS decoding and
Foxglove transport. The default now preserves the advertised bandwidth.

Existing October 27 images need the updated `uvc.conf` copied to
`/etc/modprobe.d/uvc.conf`, followed by the reload above or a reboot. An AOS
application deployment does not update this OS configuration. The SDK and
application ABI are unchanged; no sysroot re-export is needed for this fix.

From this checkout on the development host (adjust the target address if needed):

```sh
scp layers/meta-tegrademo/recipes-aos/configuration/aos-configuration/contents/etc/modprobe.d/uvc.conf \
  pi@10.18.68.101:/home/pi/uvc.conf
ssh pi@10.18.68.101
```

Then on the Orin, stop any bench capture as well as the production service:

```sh
sudo systemctl stop aos.service
sudo cp -a --no-clobber /etc/modprobe.d/uvc.conf /etc/modprobe.d/uvc.conf.before-camera-fix
sudo install -m 0644 /home/pi/uvc.conf /etc/modprobe.d/uvc.conf
sudo modprobe -r uvcvideo
sudo modprobe uvcvideo
cat /sys/module/uvcvideo/parameters/bandwidth_quirk_divisor
```

The final command must print `1`. If the module is busy, stop the remaining
camera applications before retrying, or reboot after installing the file.
Restart production AOS only once its actual robot profile and calibration are
configured. The software repository's `tools/orin_pipeline_smoke/README.md`
describes an isolated live-camera test that does not require that configuration.

A bandwidth reduction is a camera-specific workaround and needs validation
with the actual camera set and mode. Serial tests of all four ports do not
establish four simultaneous streams. The divisor is read-only after module
load; zero is treated as one to avoid a kernel divide-by-zero.
