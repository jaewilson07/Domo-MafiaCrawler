
{ pkgs }: {
  deps = [
    pkgs.nodejs-20
    pkgs.python311
    pkgs.alsa-lib
    pkgs.at-spi2-atk
    pkgs.at-spi2-core
    pkgs.atk
    pkgs.cairo
    pkgs.cups
    pkgs.dbus
    pkgs.expat
    pkgs.gbm
    pkgs.gtk3
    pkgs.libdrm
    pkgs.libudev-zero
    pkgs.libxkbcommon
    pkgs.mesa
    pkgs.nspr
    pkgs.nss
    pkgs.pango
    pkgs.systemd
    pkgs.xorg.libX11
    pkgs.xorg.libXcomposite
    pkgs.xorg.libXdamage
    pkgs.xorg.libXext
    pkgs.xorg.libXfixes
    pkgs.xorg.libXrandr
    pkgs.xorg.libxcb
    # Extra dependencies for web crawling
    pkgs.chromium
    pkgs.firefox
    pkgs.playwright-driver.browsers
    pkgs.postgresql
    pkgs.xvfb-run
  ];
}
