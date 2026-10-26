FROM debian:13-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash bc bison build-essential ca-certificates chrpath cpio curl diffstat \
    file flex gawk git iproute2 iputils-ping libegl1 libsdl2-dev locales \
    lz4 openssh-client patch python3 python3-apt python3-absl python3-jinja2 \
    python3-pexpect python3-pip rpcsvc-proto rsync socat texinfo unzip \
    util-linux wget xfsprogs xz-utils zstd \
    && sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen && rm -rf /var/lib/apt/lists/*
ENV LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# Match the checkout owner so build output remains editable on the host.
ARG BUILD_UID=1000
ARG BUILD_GID=1000
RUN groupadd --gid ${BUILD_GID} builder \
    && useradd --uid ${BUILD_UID} --gid ${BUILD_GID} --create-home builder
USER builder
WORKDIR /work
CMD ["bash"]
