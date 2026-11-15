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

      # The one place the Android versions are defined. Platform, build-tools and
      # system image all derive from these; matches Paseo's docs/android.md.
      android = rec {
        platform = "35";
        buildTools = "${android.platform}.0.0";
        systemImageType = "google_apis";
        abi = "x86_64";
      };

      # Evaluated only when the android shell is requested: it needs unfree
      # and licensed packages, and the default shell must not fetch any of it.
      androidShell =
        let
          apkgs = import nixpkgs {
            inherit system;
            config = {
              allowUnfree = true;
              android_sdk.accept_license = true;
            };
          };
          composition = apkgs.androidenv.composeAndroidPackages {
            platformVersions = [ android.platform ];
            buildToolsVersions = [ android.buildTools ];
            includeEmulator = true;
            includeSystemImages = true;
            systemImageTypes = [ android.systemImageType ];
            abiVersions = [ android.abi ];
          };
          sdk = composition.androidsdk;
          jdk = apkgs.jdk21;
        in
        pkgs.mkShell {
          packages = base ++ [
            jdk
            (apkgs.gradle.override { java = jdk; })
            sdk
          ];
          JAVA_HOME = "${jdk}";
          ANDROID_HOME = "${sdk}/libexec/android-sdk";
          ANDROID_SDK_ROOT = "${sdk}/libexec/android-sdk";
          ANDROID_PLATFORM = android.platform;
          ANDROID_BUILD_TOOLS = android.buildTools;
        };

      paseo-install = helper "paseo-install" [ ];
      paseo-dev-smoke = helper "paseo-dev-smoke" [ ];
      paseo-desktop-capture = helper "paseo-desktop-capture" [ ];

      # jq reads the Playwright version from the checkout's lock file. Node
      # comes from the shell's PATH, so the check reports the shell's Node.
      paseo-dev-check = helper "paseo-dev-check" [ pkgs.jq ];

      base = [
        pkgs.nodejs_22
        pkgs.python3
        pkgs.gcc
        pkgs.gnumake
        pkgs.pkg-config
        pkgs.xvfb-run
        pkgs.xorg-server
        paseo-install
        paseo-dev-smoke
        paseo-dev-check
        paseo-desktop-capture
      ];
    in
    {
      devShells.${system} = {
        default = pkgs.mkShell { packages = base; };
        android = androidShell;
      };
    };
}
