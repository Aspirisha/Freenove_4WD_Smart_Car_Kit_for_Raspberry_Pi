{
  description = "Dev environment for Freenove car project";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";

  outputs = { self, nixpkgs }:
    let
      system = "aarch64-darwin";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          pkgs.python312

          # Prebuilt Python packages with native code (avoids LC_RPATH issues)
          pkgs.python312Packages.numpy
          pkgs.python312Packages.opencv4

          (pkgs.python312.withPackages (ps: with ps; [
            pyqt5
            setuptools
            wheel
            ipython
            pip      # for installing pure Python packages
          ]))
          pkgs.qt5.full
          pkgs.gfortran
        ];

        shellHook = ''
          echo "🐍 Python $(python --version) ready with PyQt5 + NumPy"
          echo "🖼  You can now run 'designer' (Qt Designer GUI)"
          export PATH=$PATH:${pkgs.qt5.full}/bin
          alias designer='open ${pkgs.qt5.full}/bin/Designer.app'
          if [ -f $(nix eval --raw nixpkgs#bash-completion)/share/bash-completion/bash_completion ]; then
            source $(nix eval --raw nixpkgs#bash-completion)/share/bash-completion/bash_completion
          fi
        '';
      };
    };
}