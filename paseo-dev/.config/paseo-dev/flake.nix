# Personal dev environment for working on Paseo. Independent of Paseo's own
# flake: nothing here imports it, so a checkout's path never enters the inputs.
# Design: docs/superpowers/specs/2026-11-14-paseo-nix-flake-dev-environment-design.md
{
  description = "Personal dev environment for Paseo";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      # Helpers on PATH inside the shell. Sources live in scripts/.
      helper =
        name: runtimeInputs:
        pkgs.writeShellApplication {
          inherit name runtimeInputs;
          text = builtins.readFile ./scripts/${name}.sh;
        };

      paseo-install = helper "paseo-install" [ ];
      paseo-dev-smoke = helper "paseo-dev-smoke" [ ];
      # jq reads the Playwright version from the checkout's lock file. Node
      # comes from the shell's PATH, so the check reports the shell's Node.
      paseo-dev-check = helper "paseo-dev-check" [ pkgs.jq ];
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          pkgs.nodejs_22
          pkgs.python3
          pkgs.gcc
          pkgs.gnumake
          pkgs.pkg-config
          paseo-install
          paseo-dev-smoke
          paseo-dev-check
        ];
      };
    };
}
