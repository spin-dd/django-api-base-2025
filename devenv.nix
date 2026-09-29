{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

{
  languages.python = {
    enable = true;
    version = "3.12";
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  dotenv.enable = true;

  # mysqlclient と WeasyPrint のビルドに必要なシステム依存
  packages = [
    # MySQL
    pkgs.libmysqlclient
    pkgs.libmysqlclient.dev
    pkgs.pkg-config
    pkgs.openssl

    # Linter / Formatter / LSP
    pkgs.ruff
    pkgs.basedpyright
    pkgs.nixfmt-rfc-style
    pkgs.treefmt
  ];

  # mysqlclient ビルド用の環境変数
  env = {
    MYSQLCLIENT_CFLAGS = "-I${pkgs.libmysqlclient.dev}/include/mariadb";
    MYSQLCLIENT_LDFLAGS = "-L${pkgs.libmysqlclient}/lib/mariadb -lmariadb";
  };

  # pre-commit hooks
  pre-commit.hooks = {
    # Ruff linter (pyproject.toml の設定を自動で読み込む)
    ruff.enable = true;
    # Ruff formatter
    ruff-format.enable = true;
    # Nix formatter
    nixfmt-rfc-style.enable = true;
  };

  enterShell = ''
    echo "🐍 Python $(python --version | cut -d' ' -f2)"
    echo "📦 uv $(uv --version | cut -d' ' -f3)"
    echo "🗄️  mariadb_config: $(which mariadb_config)"
    echo ""
    echo "🔧 Dev tools:"
    echo "   ruff $(ruff --version | head -1)"
    echo "   basedpyright $(basedpyright --version)"
    echo ""
    echo "📝 Commands:"
    echo "   treefmt               # format all (nix, python)"
    echo "   ruff check .          # lint"
    echo "   ruff format .         # format python"
    echo "   basedpyright          # type check (LSP)"
    echo "   uv run mypy apibase   # type check (mypy)"
    echo "   pre-commit run --all  # run all hooks"
  '';
}
