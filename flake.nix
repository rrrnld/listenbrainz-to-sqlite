{
  description = "Application packaged using poetry2nix";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    {
      # Nixpkgs overlay providing the application
      overlay = nixpkgs.lib.composeManyExtensions [
        poetry2nix.overlay
        (final: prev: {
          # The application
          datasetteListenbrainzImporter = prev.poetry2nix.mkPoetryApplication {
            projectDir = ./.;
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

        defaultApp = apps.datasetteListenbrainzImporter;

        devShell = pkgs.mkShell rec {
          buildInputs = with pkgs; [
            (python3.withPackages(ps: with ps; [
              pip
              poetry
              black
            ]))
          ];
       };
      }));
}
