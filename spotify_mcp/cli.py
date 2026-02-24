"""Interactive setup wizard for Spotify MCP."""

import os
import sys
from pathlib import Path


def setup():
    """Run the interactive setup wizard."""
    print("Spotify MCP Setup")
    print("=" * 40)
    print()
    print("You'll need a Spotify Developer App.")
    print("Create one at: https://developer.spotify.com/dashboard")
    print()

    client_id = input("Spotify Client ID: ").strip()
    if not client_id:
        print("Error: Client ID is required.")
        sys.exit(1)

    client_secret = input("Spotify Client Secret: ").strip()
    if not client_secret:
        print("Error: Client Secret is required.")
        sys.exit(1)

    redirect_uri = input(
        "Redirect URI [http://127.0.0.1:8888/callback]: "
    ).strip() or "http://127.0.0.1:8888/callback"

    # Determine config directory
    if sys.platform == "win32":
        config_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "spotify-mcp"
    else:
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "spotify-mcp"

    config_dir.mkdir(parents=True, exist_ok=True)
    env_path = config_dir / ".env"

    env_content = (
        f"SPOTIFY_CLIENT_ID={client_id}\n"
        f"SPOTIFY_CLIENT_SECRET={client_secret}\n"
        f"SPOTIFY_REDIRECT_URI={redirect_uri}\n"
    )

    env_path.write_text(env_content)
    print(f"\nCredentials saved to {env_path}")

    # Trigger OAuth flow
    print("\nOpening browser for Spotify authorization...")
    print("(Grant access, then return here)")
    print()

    # Set env vars so config.py picks them up
    os.environ["SPOTIFY_CLIENT_ID"] = client_id
    os.environ["SPOTIFY_CLIENT_SECRET"] = client_secret
    os.environ["SPOTIFY_REDIRECT_URI"] = redirect_uri

    try:
        from .auth import get_spotify_client
        client = get_spotify_client()
        me = client.me()
        print(f"Authorized as: {me.get('display_name', 'Unknown')} ({me.get('id', '')})")
    except Exception as e:
        print(f"Authorization failed: {e}")
        print("You can retry later — credentials are saved.")

    # Print Claude Desktop config
    print()
    print("=" * 40)
    print("Add this to your claude_desktop_config.json:")
    print()
    print("""{
  "mcpServers": {
    "spotify": {
      "command": "uvx",
      "args": ["spotify-mcp"]
    }
  }
}""")
    print()
    print("Setup complete!")
