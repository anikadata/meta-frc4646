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

### Local validation (2026-10-26)

The complete `demo-image-base` build for `p3768-0000-p3767-0003` passed all
11,549 tasks, including image QA. The local artifact is
`../artifacts/orin-nano-8gb-2026.10.26.tegraflash-tar.zst`; its checksum is in
`../artifacts/SHA256SUMS`. The archive contains `initrd-flash`, the ext4 image,
and the SKU 0003 device tree. Its flash configuration checks board 3767 / SKU 0003.

The assembled image contains the enabled filesystem-growth fix and utilities,
`ldd`, camera aliases, SCTP, and the UVC bandwidth parameter. The paired AOS
bundle passed 28 native loader checks and recorded-image MONO8/YUYV CUDA tests
on the connected Orin. The new image has not been flashed; live camera and
roboRIO integration remain untested. See `../artifacts/bringup-state.json` and
the software repository's `tools/wrynose_sysroot/README.md` for validation details.


To view the serial console:
```
python3 /usr/lib/python3/dist-packages/serial/tools/miniterm.py /dev/ttyUSB0 115200
```

# AOS compatibility before flashing

This image pins CUDA 13.2 and OpenCV 4.13. The paired software branch
`team1868/software:anikadata/newsysrootwrynose` selects a matching
Wrynose export instead of Walnascar (CUDA 12.6 / OpenCV 4.11). Install that
local sysroot and rebuild the AOS bundle; see `tools/wrynose_sysroot/README.md`
and `2026/vision/README.md` in the software repository. Missing
`libcudart.so.12` or `libopencv_*.so.411` on the Orin indicates old binaries;
reflashing alone does not fix them.

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

To turn quirks on to fix bandwidth calcs:

```
rmmod uvcvideo
modprobe uvcvideo quirks=128 bandwidth_quirk_divisor=16
```

`dmesg` will spit out frame statistics, including bandwidth usage.

The image's `uvc.conf` sets these parameters. The divisor is a camera-specific
bandwidth workaround, not evidence that four simultaneous streams will fit.
Check all four streams at the configured resolution and frame rate. The
divisor is read-only after module load; zero is treated as one to avoid a
kernel divide-by-zero.
