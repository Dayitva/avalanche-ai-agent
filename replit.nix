{pkgs}: {
  deps = [
    pkgs.solc
    pkgs.rustc
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.libiconv
    pkgs.cargo
    pkgs.openssl
    pkgs.postgresql
  ];
}
