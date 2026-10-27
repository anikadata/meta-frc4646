FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    bmap-tools bzip2 ca-certificates cpio device-tree-compiler dosfstools e2fsprogs file gdisk libxml2-utils \
    lz4 openssl parted python3 python3-cryptography python3-pycryptodome python3-yaml \
    udev usbutils util-linux xxd xz-utils zstd \
    && rm -rf /var/lib/apt/lists/*
COPY check_dependencies.py /usr/local/lib/orin-flash-check.py
WORKDIR /flash
ENTRYPOINT ["./initrd-flash"]
