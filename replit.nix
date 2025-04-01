
{pkgs}: {
  deps = [
    pkgs.postgresql
    pkgs.openssl
    pkgs.playwright-driver.browsers
    pkgs.xvfb-run
    pkgs.firefox
    pkgs.chromium
    pkgs.nss
    pkgs.nspr
    pkgs.dbus
    pkgs.atk
    pkgs.at-spi2-atk
    pkgs.cups
    pkgs.expat
    pkgs.xorg.libXcomposite
    pkgs.xorg.libXdamage
    pkgs.xorg.libXfixes
    pkgs.mesa
    pkgs.xorg.libxcb
    pkgs.xkbcommon
    pkgs.pango
    pkgs.cairo
    pkgs.udev
    pkgs.alsa-lib
    pkgs.at-spi2-core
  ];
}
