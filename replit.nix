
{ pkgs }: {
    deps = [
      pkgs.playwright
      pkgs.python311Packages.playwright
      pkgs.at-spi2-core
      pkgs.at-spi2-atk
      pkgs.systemd
      pkgs.alsa-lib
      pkgs.libxkbcommon
      pkgs.gtk3
      pkgs.xorg.libxcb
      pkgs.mesa
      pkgs.expat
      pkgs.dbus
      pkgs.nspr
      pkgs.nss
      pkgs.xorg.libXfixes
      pkgs.xorg.libXdamage
      pkgs.xorg.libXcomposite
      pkgs.playwright-driver
      pkgs.gitFull
        pkgs.python311
        pkgs.python311Packages.pip
        pkgs.python311Packages.flask
        pkgs.python311Packages.gunicorn
        pkgs.python311Packages.requests
        pkgs.python311Packages.beautifulsoup4
        pkgs.python311Packages.psycopg2
        pkgs.nodejs_20
        # Development tools
        pkgs.nodePackages.typescript
        pkgs.git
        pkgs.chromium
        pkgs.firefox
        pkgs.playwright-driver.browsers
        pkgs.postgresql
        pkgs.xvfb-run
    ];
    env = {
        PYTHONPATH = "${pkgs.python311}/bin/python3";
        PIP_DISABLE_PIP_VERSION_CHECK = "1";
        PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright-driver.browsers}";
        PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = true;
    };
}
