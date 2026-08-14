DISTRO = "tegrademo"
DISTRO_NAME = "OE4Tegra Demonstration Distro"
DISTRO_VERSION_BASE = "6.0.2"
DISTRO_VERSION = "${DISTRO_VERSION_BASE}+snapshot-${METADATA_REVISION}"
DISTRO_CODENAME = "wrynose"
SDK_VENDOR = "-tdsdk"
SDK_VERSION = "${@d.getVar('DISTRO_VERSION').replace('snapshot-${METADATA_REVISION}', 'snapshot')}"
SDK_VERSION[vardepvalue] = "${SDK_VERSION}"

MAINTAINER = "OE4Tegra team <oe4tegra@madison.systems>"

TARGET_VENDOR = "-oe4t"

# New ${DISTRO}-<version> setting for sanity checks.
# Increment version number (and the corresponding
# setting int the template bblayers.conf.sample file)
# each time the layer settings are changed.
REQUIRED_TD_BBLAYERS_CONF_VERSION = "${DISTRO}-7"

LOCALCONF_VERSION = "2"

TD_DEFAULT_DISTRO_FEATURES = "opencl pam virtualization"
DISTRO_FEATURES ?= "${TD_DEFAULT_DISTRO_FEATURES}"

DISTRO_FEATURES_OPTED_OUT += "ptest vulkan"

# Jetson platforms do not use linux-yocto, but for QEMU testing
# align with the poky distro.
#TEGRA_DEFAULT_KERNEL ?= "linux-yocto"
#PREFERRED_PROVIDER_virtual/kernel:tegra = "${TEGRA_DEFAULT_KERNEL}"

SDK_NAME = "${DISTRO}-${TCLIBC}-${SDKMACHINE}-${IMAGE_BASENAME}-${TUNE_PKGARCH}-${MACHINE}"
SDKPATHINSTALL = "/opt/${DISTRO}/${SDK_VERSION}"

PACKAGE_CLASSES ?= "package_deb"

SANITY_TESTED_DISTROS ?= " \
            debian-12 \n \
            debian-13 \n \
            "

# Most NVIDIA-supplied services expect systemd
INIT_MANAGER = "systemd"

LICENSE_FLAGS_ACCEPTED += "commercial_faad2 commercial_x264"

USE_REDUNDANT_FLASH_LAYOUT_DEFAULT ?= "0"
