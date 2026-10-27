FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    bmap-tools bzip2 ca-certificates cpio dosfstools e2fsprogs file gdisk libxml2-utils \
    lz4 openssl parted python3 python3-cryptography python3-pycryptodome \
    udev usbutils util-linux xxd xz-utils zstd \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /flash
ENTRYPOINT ["./initrd-flash"]
