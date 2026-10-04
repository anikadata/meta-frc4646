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

The upstream project has been modified to support AOS on the Jetson Nano 8GB SOM on a Seeed
studio J401. Confirm the carrier and module before selecting a machine;
`p3768-0000-p3767-0003` describes an 8GB production module on a P3768 carrier.
Build on Linux with a case-sensitive build filesystem. To build, run:

```
export MACHINE=p3768-0000-p3767-0003
. layers/oe-init-build-env build
bitbake demo-image-base && ../to_xfs.py tmp/deploy/images/p3768-0000-p3767-0003/demo-image-base-p3768-0000-p3767-0003.rootfs.tegraflash.tar.gz demo-image-base-p3768-0000-p3767-0003.rootfs.tegraflash.tar.zst
```

Note: this hasn't been tested yet with a fresh checkout, not everything might be captured yet.

To flash, extract the image, then run `sudo ./initrd-flash` with the orin in bootloader mode, connected over USB.

To build for a devkit instead of a seed J401, run:
```
export MACHINE=jetson-orin-nano-devkit-nvme
. layers/oe-init-build-env build
bitbake demo-image-base && ../to_xfs.py tmp/deploy/images/jetson-orin-nano-devkit-nvme/demo-image-base-jetson-orin-nano-devkit-nvme.rootfs.tegraflash.tar.gz demo-image-base-jetson-orin-nano-devkit-nvme.rootfs.tegraflash.tar.zst
```

And flash the same way, with ./initrd-flash


To view the serial console:
```
python3 /usr/lib/python3/dist-packages/serial/tools/miniterm.py /dev/ttyUSB0 115200
```

# AOS compatibility before flashing

This image pins CUDA 13.2 and OpenCV 4.13. Local changes on the software
branch `team1868/software:anikadata/newsysrootwrynose` now select a matching
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
