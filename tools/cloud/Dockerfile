FROM debian:trixie-slim@sha256:a29215f6a35e51e22adffa17f89e9d2ef06214e64a2bad10d765c46aea49f11f
ENV DEBIAN_FRONTEND=noninteractive \
    PATH=/opt/wine/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    WINEPREFIX=/home/editor/.wine WINEARCH=win64 WINEDLLOVERRIDES="mscoree,mshtml,winegstreamer="
# Keep filesystem changes in one large layer: the cloud daemon uses the VFS driver.
WORKDIR /home/editor
COPY . /tmp/setup/
RUN dpkg --add-architecture i386 \
 && sed -i s,http://deb.debian.org,https://deb.debian.org,g /etc/apt/sources.list.d/debian.sources \
 && apt-get -o Acquire::https::CaInfo=/tmp/setup/build-ca.pem update --error-on=any \
 && apt-get -o Acquire::https::CaInfo=/tmp/setup/build-ca.pem install -y --no-install-recommends \
    wine wine64 wine32:i386 wine32-preloader:i386 qemu-user xvfb xauth x11-utils xdotool imagemagick unzip xz-utils ca-certificates \
    fonts-liberation fonts-crosextra-carlito fonts-dejavu-core procps \
 && mv /usr/lib/wine/wine /usr/lib/wine/wine.real \
 && printf '#!/bin/sh\nexec /usr/bin/qemu-i386 /usr/lib/wine/wine.real "$@"\n' > /usr/lib/wine/wine \
 && rm /usr/lib/wine/wine-preloader \
 && printf '#!/bin/sh\nexec /usr/bin/qemu-i386 /usr/lib/wine/wine-preloader.static "$@"\n' > /usr/lib/wine/wine-preloader \
 && chmod 755 /usr/lib/wine/wine /usr/lib/wine/wine-preloader \
 && mkdir -p /opt/wine /opt/dotnet /opt/hma /opt/am /opt/xse \
 && tar -xJf /tmp/setup/packages/wine-11.0-amd64-wow64.tar.xz -C /opt/wine --strip-components=1 \
 && unzip -oq /tmp/setup/packages/dotnet-runtime-6.0.36-win-x64.zip -d /opt/dotnet \
 && unzip -oq /tmp/setup/packages/windowsdesktop-runtime-6.0.36-win-x64.zip -d /opt/dotnet \
 && unzip -oq /tmp/setup/packages/HexManiacAdvance_x64.0.5.6.1.debug.zip -d /opt/hma \
 && unzip -oq /tmp/setup/packages/advancedMap-1.95.zip -d /opt/am \
 && unzip -oq /tmp/setup/packages/XSE-archived.zip -d /opt/xse \
 && cp /tmp/setup/packages/msvbvm60.dll /opt/xse/ \
 && cp -R /tmp/setup/Fonts /opt/font-aliases \
 && cp /tmp/setup/entrypoint.sh /usr/local/bin/leafgreen-editor \
 && chmod -R a+rX /opt/wine /opt/dotnet /opt/hma /opt/am /opt/xse /opt/font-aliases \
 && chmod 755 /usr/local/bin/leafgreen-editor \
 && useradd --create-home --uid 1000 editor \
 && chown editor:editor /home/editor \
 && rm -rf /var/lib/apt/lists/* /tmp/setup
USER editor
ENTRYPOINT ["/usr/local/bin/leafgreen-editor"]
CMD ["runtimes"]
