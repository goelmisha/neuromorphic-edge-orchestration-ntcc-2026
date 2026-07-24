{
  description = "Elastic Lava Runtime Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # Pull in an older release specifically for Python 3.10
    nixpkgs-old.url = "github:NixOS/nixpkgs/nixos-23.11";
  };

  outputs = { self, nixpkgs, nixpkgs-old }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
    pkgsOld = import nixpkgs-old { inherit system; };

    # Grab Python 3.10 from the older package set
    pythonEnv = pkgsOld.python310.withPackages (ps: with ps; [
      numpy
      scipy
      pyzmq
      psutil
      cryptography
      redis
      pandas
      matplotlib
      rich
      pip
    ]);
  in {
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = [
        pythonEnv
        pkgs.zeromq
        pkgs.wireguard-tools
        pkgs.tailscale
        pkgs.criu
        pkgs.tmux
      ];
      shellHook = ''
        export PYTHONPATH="${pythonEnv}/lib/python3.10/site-packages:$PYTHONPATH"
        echo "Lava Neuromorphic Environment Loaded. Parity: Deterministic."
      '';
    };
  };
}
