{
  description = "Application packaged using poetry2nix";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";
  inputs.poetry2nix = {
    url = "github:nix-community/poetry2nix";
    inputs = {
      nixpkgs.follows = "nixpkgs";
      flake-utils.follows = "flake-utils";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    {
      # Nixpkgs overlay providing the application
      overlay = nixpkgs.lib.composeManyExtensions [
        poetry2nix.overlay
        (final: prev: {
          # The application
          datasetteListenbrainzImporter = prev.poetry2nix.mkPoetryApplication {
            projectDir = ./.;
            overrides = prev.poetry2nix.defaultPoetryOverrides.extend ( self: super: {
              diff-cover = super.diff-cover.overridePythonAttrs (
                old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ self.poetry ];
                }
              );

              datasette = super.datasette.overridePythonAttrs (
                old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ self.pytest-runner ];
                }
              );
            });
          };
        })
      ];
    } // (flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlay ];
        };
      in
      rec {
        apps = {
          datasetteListenbrainzImporter = pkgs.datasetteListenbrainzImporter;
        };

        defaultApp = pkgs.datasetteListenbrainzImporter;

        devShell = pkgs.mkShell rec {
          buildInputs = with pkgs; [
            (python3.withPackages(ps: with ps; [
              black
              pip
              poetry
              pyright
            ]))
          ];
       };
      }));
}
