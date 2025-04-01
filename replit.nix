
{pkgs}: {
  deps = [
    pkgs.postgresql
    pkgs.openssl
    pkgs.playwright-driver.browsers
    pkgs.xvfb-run
    pkgs.firefox
    pkgs.chromium
  ];
}
