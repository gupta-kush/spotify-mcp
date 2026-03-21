# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | Yes                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it through [GitHub Security Advisories](https://github.com/gupta-kush/spotify-mcp/security/advisories/new).

**Please do not open a public issue for security vulnerabilities.**

We will acknowledge your report within 48 hours and provide a timeline for a fix.

## Credential Safety

- Never commit `.env` files or Spotify tokens to version control
- The `.gitignore` excludes `.env` and `.spotify_token_cache` by default
- Credentials are stored in your platform's user config directory, not in the project
- If you accidentally expose credentials, rotate them immediately in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
