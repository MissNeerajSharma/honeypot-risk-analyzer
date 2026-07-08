# Honeyd has no maintained Docker Hub image (it's a 2007-era C daemon),
# so this builds it from source — the same approach used by community
# Dockerfiles (e.g. carlsaturnino/docker-honeyd).
#
# Build:
#   docker build -t lab-honeyd ./honeyd
#
# Honeyd needs raw-socket access to forge packets, so the compose service
# grants NET_ADMIN + NET_RAW (see ../docker-compose.yml).

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    autoconf \
    automake \
    libtool \
    bison \
    flex \
    libevent-dev \
    libdumbnet-dev \
    libpcap-dev \
    libpcre3-dev \
    libedit-dev \
    zlib1g-dev \
    net-tools \
    iputils-ping \
    python3 \
    iptables \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/DataSoft/Honeyd.git /opt/honeyd-src

WORKDIR /opt/honeyd-src

# Honeyd's post-install script (scripts/lib/init.py) uses Python 2's octal
# literal syntax (e.g. 0666), which is a hard SyntaxError in Python 3 —
# there's no python2 available on Ubuntu 22.04 to fall back to, so patch
# the literals to Python 3's 0o666 form instead.
RUN sed -i -E 's/\b0([0-7]{3,4})\b/0o\1/g' scripts/lib/init.py

# GCC 10+ changed its default from -fcommon to -fno-common, which breaks
# Honeyd's 2007-era code (it declares global variables in headers without
# `extern`, relying on the old "common symbol" linking behavior) — you'll
# see "multiple definition of libevent_base" and similar linker errors
# without it.
#
# IMPORTANT: don't set CFLAGS before running ./configure. Honeyd's
# configure.in only injects its own required defines (PATH_HONEYDDATA,
# PATH_RRDTOOL, etc.) into CFLAGS when CFLAGS is *unset* — pre-setting it
# (e.g. CFLAGS="-fcommon" ./configure) causes configure to skip that step
# entirely, and the build fails with "PATH_HONEYDDATA undeclared" instead.
# So: let configure compute its own full CFLAGS first, then patch the
# generated Makefile to add -fcommon alongside it.
RUN ./autogen.sh && \
    ./configure && \
    sed -i 's/^CFLAGS = /CFLAGS = -fcommon /' Makefile && \
    make && \
    make install

COPY honeyd.conf /etc/honeyd/honeyd.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 21 22 23 80

# -d: don't daemonize (keep container attached to logs)
# -i eth0: bind to the container's own interface (no extra virtual IPs
#          needed for a single-personality lab honeypot)
CMD ["/entrypoint.sh"]
