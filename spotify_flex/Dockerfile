ARG BUILD_FROM=lscr.io/linuxserver/daapd:latest

# ---- go-librespot (Spotify Connect receiver) --------------------------------
FROM golang:1.25-alpine AS golibrespot
ARG GLR_VERSION=v0.9.1
RUN apk add --no-cache git gcc musl-dev pkgconf alsa-lib-dev libogg-dev libvorbis-dev flac-dev mpg123-dev
RUN git clone --depth 1 --branch "${GLR_VERSION}" https://github.com/devgianlu/go-librespot /src
WORKDIR /src
RUN CGO_ENABLED=1 go build -trimpath -ldflags "-s -w" -o /out/go-librespot ./cmd/daemon
# bundle the shared libraries so the binary does not depend on the runtime image's versions
RUN mkdir -p /out/lib \
 && ldd /out/go-librespot | awk '/=>/ {print $3}' | grep -v 'ld-musl' | xargs -r -I{} cp -L {} /out/lib/

# ---- runtime: OwnTone (AirPlay 2 sender) from linuxserver/daapd -------------
FROM ${BUILD_FROM}
RUN apk add --no-cache python3 py3-aiohttp
COPY --from=golibrespot /out/go-librespot /opt/golibrespot/go-librespot
COPY --from=golibrespot /out/lib /opt/golibrespot/lib
COPY rootfs /
# the image's own rust librespot is replaced by go-librespot
RUN rm -f /etc/s6-overlay/s6-rc.d/user/contents.d/svc-librespot \
 && chmod +x /etc/s6-overlay/s6-rc.d/init-flex-config/run \
             /etc/s6-overlay/s6-rc.d/svc-golibrespot/run \
             /etc/s6-overlay/s6-rc.d/svc-flexui/run \
 && LD_LIBRARY_PATH=/opt/golibrespot/lib /opt/golibrespot/go-librespot --help >/dev/null 2>&1 || true \
 && python3 -c "import aiohttp; print('aiohttp', aiohttp.__version__)"

LABEL io.hass.type="addon" io.hass.version="1.0.0"
