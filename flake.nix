{
  description = "Elastic Lava Runtime Environment";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: let
    pkgs = import nixpkgs { system = "x86_64-linux"; };
    # Bumped directly to python314 to clear the sphinx restriction
    pythonEnv = pkgs.python314.withPackages (ps: with ps; [
      numpy
      scipy
      pyzmq
      psutil
      cryptography
      redis
      pandas
      matplotlib
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
        pkgs.tmux
      ];
      shellHook = ''
        # Path updated to match python3.14
        export PYTHONPATH="${pythonEnv}/lib/python3.14/site-packages:$PYTHONPATH"
        echo "Lava Neuromorphic Environment Loaded. Parity: Deterministic."
      '';
    };
  };
}
