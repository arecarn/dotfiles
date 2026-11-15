# Personal dev environment for working on Paseo. Independent of Paseo's own
# flake: nothing here imports it, so a checkout's path never enters the inputs.
# See README.md in this directory for the first-time sequence and pin updates.
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

      # The one place the Node and Java majors are defined. Each shell exports
      # them (PASEO_DEV_NODE_MAJOR, PASEO_DEV_JAVA_MAJOR) so the smoke script
      # asserts the same values. Keep them in step with Paseo's .tool-versions;
      # paseo-dev-check reports Node drift against it.
      nodeMajor = "22";
      javaMajor = "21";

      # The one place the Android versions are defined. Platform, build-tools and
      # system image all derive from these; they follow Paseo's docs/android.md.
      android = rec {
        platform = "36";
        buildTools = "${android.platform}.0.0";
        systemImageType = "google_apis";
        abi = "x86_64";
        # Not in docs/android.md: React Native's Gradle plugin asks for this
        # NDK (react-native's libs.versions.toml ndkVersion) and cannot install
        # it into the read-only SDK. Bump it when React Native does.
        ndk = "27.1.12297006";
        # Also not in docs/android.md: the Expo module Gradle plugin builds
        # with these build-tools whatever Paseo's compileSdk is.
        expoBuildTools = "35.0.0";
        # The native modules (react-native-nitro-modules) ask AGP for this CMake.
        cmake = "3.22.1";
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
            buildToolsVersions = [ android.buildTools android.expoBuildTools ];
            includeEmulator = true;
            includeSystemImages = true;
            systemImageTypes = [ android.systemImageType ];
            abiVersions = [ android.abi ];
            includeNDK = true;
            ndkVersions = [ android.ndk ];
            includeCmake = true;
            cmakeVersions = [ android.cmake ];
          };
          sdk = composition.androidsdk;
          jdk = apkgs."jdk${javaMajor}";
        in
        pkgs.mkShell {
          packages = base ++ [
            (helper "paseo-emulator" [ ])
            jdk
            (apkgs.gradle.override { java = jdk; })
            sdk
          ];
          PASEO_DEV_NODE_MAJOR = nodeMajor;
          PASEO_DEV_JAVA_MAJOR = javaMajor;
          JAVA_HOME = "${jdk}";
          ANDROID_HOME = "${sdk}/libexec/android-sdk";
          ANDROID_SDK_ROOT = "${sdk}/libexec/android-sdk";
          ANDROID_PLATFORM = android.platform;
          ANDROID_BUILD_TOOLS = android.buildTools;
          ANDROID_SYSTEM_IMAGE_TYPE = android.systemImageType;
          ANDROID_ABI = android.abi;
          ANDROID_NDK_VERSION = android.ndk;
        };

      paseo-install = helper "paseo-install" [ ];
      paseo-playwright-install = helper "paseo-playwright-install" [ ];
      paseo-dev-smoke = helper "paseo-dev-smoke" [ ];
      paseo-desktop-capture = helper "paseo-desktop-capture" [ ];

      # jq reads the Playwright version from the checkout's lock file. Node
      # comes from the shell's PATH, so the check reports the shell's Node.
      paseo-dev-check = helper "paseo-dev-check" [ pkgs.jq ];

      base = [
        pkgs."nodejs_${nodeMajor}"
        pkgs.python3
        pkgs.gcc
        pkgs.gnumake
        pkgs.pkg-config
        pkgs.xvfb-run
        # xvfb-run alone works, but it keeps Xvfb off PATH; the smoke asserts it.
        pkgs.xorg-server
        paseo-install
        paseo-playwright-install
        paseo-dev-smoke
        paseo-dev-check
        paseo-desktop-capture
      ];
    in
    {
      devShells.${system} = {
        default = pkgs.mkShell {
          packages = base;
          PASEO_DEV_NODE_MAJOR = nodeMajor;
        };
        android = androidShell;
      };
    };
}
