#!/bin/sh
set -eu
app=${1:-runtimes}
shift || true
mkdir -p /home/editor/logs
if [ -z "${DISPLAY:-}" ]; then
    export DISPLAY=:99
    Xvfb "$DISPLAY" -screen 0 1280x900x24 -nolisten tcp > /home/editor/logs/xvfb.log 2>&1 &
    attempts=0
    until xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; do
        attempts=$((attempts + 1))
        [ "$attempts" -lt 30 ] || { echo 'Xvfb failed to start' >&2; exit 1; }
        sleep 0.2
    done
fi
if [ ! -f /home/editor/.leafgreen-initialized-v1 ]; then
    mkdir -p "$WINEPREFIX/drive_c/windows/Fonts"
    cp /opt/font-aliases/*.ttf "$WINEPREFIX/drive_c/windows/Fonts/"
    wineboot -i > /home/editor/logs/wineboot.log 2>&1
    for font in CalibriCompat-Regular ArialCompat SegoeUICompat TahomaCompat MSSansSerifCompat ConsolasCompat CourierNewCompat TimesNewRomanCompat; do
        wine reg add 'HKLM\Software\Microsoft\Windows NT\CurrentVersion\Fonts' \
            /v "$font (TrueType)" /t REG_SZ /d "$font.ttf" /f >> /home/editor/logs/fonts.log 2>&1
    done
    # Restart this prefix after font registration; WPF otherwise retains stale collections.
    wineserver -k
    touch /home/editor/.leafgreen-initialized-v1
fi
case "$app" in
    runtimes) exec wine /opt/dotnet/dotnet.exe --list-runtimes ;;
    hma)
        [ -d /home/editor/hma ] || cp -R /opt/hma /home/editor/hma
        cd /home/editor/hma
        exec wine /opt/dotnet/dotnet.exe HexManiacAdvance.dll "$@" ;;
    advancemap)
        [ -d /home/editor/AdvanceMap ] || cp -R /opt/am/AdvanceMap /home/editor/AdvanceMap
        cd /home/editor/AdvanceMap
        exec wine AdvanceMap.exe "$@" ;;
    xse)
        [ -d /home/editor/xse ] || cp -R /opt/xse /home/editor/xse
        cd /home/editor/xse
        exec wine XSE.exe "$@" ;;
    *) echo "Unknown tool: $app" >&2; exit 2 ;;
esac
