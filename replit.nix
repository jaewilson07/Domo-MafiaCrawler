
{ pkgs }: {
    deps = [
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
    ];
    env = {
        PYTHONPATH = "${pkgs.python311}/bin/python3";
        PIP_DISABLE_PIP_VERSION_CHECK = "1";
    };
}
