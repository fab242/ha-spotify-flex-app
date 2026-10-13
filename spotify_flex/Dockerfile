ARG BUILD_FROM=ghcr.io/home-assistant/base:3.22

# =============================================================================
# Build stage: OwnTone (AirPlay 2 sender) + go-librespot (Spotify Connect)
# Same Alpine release as the runtime image so shared-library versions match.
# =============================================================================
FROM golang:1.25-alpine3.22 AS build

ARG OWNTONE_VERSION=29.3
ARG OWNTONE_SHA256=aa0cbfc5651aa65776a8bd2112c9e0a904b2185c837900d3f6494b9ec6e8c547
ARG GLR_VERSION=v0.9.1

RUN apk add --no-cache \
      build-base pkgconf gperf bison flex git curl xz pax-utils \
      confuse-dev curl-dev libsodium-dev libxml2-dev sqlite-dev zlib-dev \
      libevent-dev json-c-dev libplist-dev ffmpeg-dev avahi-dev \
      libunistring-dev util-linux-dev libgcrypt-dev protobuf-c-dev gettext-dev \
      alsa-lib-dev libogg-dev libvorbis-dev flac-dev mpg123-dev

# --- OwnTone ------------------------------------------------------------------
RUN curl -fsSL -o /tmp/owntone.tar.xz \
      "https://github.com/owntone/owntone-server/releases/download/${OWNTONE_VERSION}/owntone-${OWNTONE_VERSION}.tar.xz" \
 && echo "${OWNTONE_SHA256}  /tmp/owntone.tar.xz" | sha256sum -c - \
 && mkdir -p /src/owntone \
 && tar xf /tmp/owntone.tar.xz -C /src/owntone --strip-components=1 \
 && cd /src/owntone \
 && ./configure \
      --prefix=/usr --sysconfdir=/etc --localstatedir=/var \
      --disable-spotify --disable-lastfm --disable-mpd --disable-webinterface \
      --disable-install-user --disable-install-systemd --disable-install-conf-file \
      --without-alsa --without-pulseaudio --without-libwebsockets --with-avahi \
 && make -j"$(nproc)" \
 && make DESTDIR=/out install \
 && rm -rf /out/usr/share /out/usr/include /out/var /out/usr/lib/owntone/*.la /out/etc

# --- go-librespot -------------------------------------------------------------
RUN git clone --depth 1 --branch "${GLR_VERSION}" https://github.com/devgianlu/go-librespot /src/go-librespot \
 && cd /src/go-librespot \
 && CGO_ENABLED=1 go build -trimpath -ldflags "-s -w" -o /out/usr/bin/go-librespot ./cmd/daemon

# --- runtime dependencies as apk "so:" providers -------------------------------
RUN scanelf --needed --nobanner --format '%n#p' --recursive /out \
      | tr ',' '\n' | sort -u \
      | awk 'system("[ -e /out/usr/lib/owntone/" $1 " ]") == 0 { next } { print "so:" $1 }' \
      > /runtime-deps.txt \
 && cat /runtime-deps.txt

# =============================================================================
# Runtime
# =============================================================================
FROM ${BUILD_FROM}

COPY --from=build /runtime-deps.txt /tmp/runtime-deps.txt
RUN apk add --no-cache python3 py3-aiohttp avahi dbus $(cat /tmp/runtime-deps.txt) \
 && { addgroup -S owntone 2>/dev/null || true; } \
 && { adduser -S -D -H -h /var/empty -G owntone owntone 2>/dev/null || true; } \
 && rm -f /tmp/runtime-deps.txt

COPY --from=build /out/ /
COPY rootfs /

RUN find /etc/s6-overlay/s6-rc.d -name run -exec chmod +x {} + \
 && chmod +x /etc/s6-overlay/s6-rc.d/init-flex/up-script \
 && (/usr/sbin/owntone -v || true) \
 && test -x /usr/bin/go-librespot \
 && python3 -c "import aiohttp; print('aiohttp', aiohttp.__version__)"
