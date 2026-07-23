{
  description = "Elastic Lava Runtime Environment";
  inputs.nixpkgs.url = "github.com/NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: let
    pkgs = import nixpkgs { system = "x86_64-linux"; };
    pythonEnv = pkgs.python310.withPackages (ps: with ps; [
      numpy
      scipy
      pyzmq
      psutil
      cryptography
      redis
      rich
    ]);
  in {
    devShells.x86_64-linux.default = pkgs.mkShell {
      buildInputs = [
        pythonEnv
        pkgs.zeromq
        pkgs.wireguard-tools
        pkgs.tailscale
        pkgs.criu
      ];
      shellHook = ''
        export PYTHONPATH="${pythonEnv}/lib/python3.10/site-packages:$PYTHONPATH"
        echo "Lava Neuromorphic Environment Loaded. Parity: Deterministic."
      '';
    };
  };
}
