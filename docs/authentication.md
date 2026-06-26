# Authentication

BookStack uses API token pairs — no OAuth, no session auth for API.

## Token Format

Every user can generate a token pair from their profile page:

```
Settings → API Tokens → Create
```

Token pair consists of:
- **Token ID** — public identifier (e.g. `a1B2c3D4e5F6g7H8i9J0k`)
- **Token Secret** — secret value shown once (e.g. `a1B2c3D4e5F6g7H8i9J0kL1m2N3o4P5q6R7s8T9u0V`)

## Request Header

```
Authorization: Token <token_id>:<token_secret>
```

Example:

```
Authorization: Token a1B2c3D4e5F6g7H8i9J0k:a1B2c3D4e5F6g7H8i9J0kL1m2N3o4P5q6R7s8T9u0V
```

## Permission Model

- Token inherits **all permissions** of the generating user's role
- No separate API-only permission scope — API access is global per user
- Content visibility matches UI: private content invisible via API
- Admin-only endpoints (users write, roles, settings) require admin role

## Security Considerations

- Token secret shown once at creation — store securely (env var, secret manager)
- No scope/restriction per token — consider dedicated service accounts
- Revoke by deleting the token from user profile
- Always use HTTPS in production

## Configuration

Config file: `~/.config/bookstack-cli/config.toml`

```toml
[connection]
url = "http://10.0.0.1:8080"                    # API endpoint (internal)
resolve_url = "https://wiki.public.example.com"  # public web URL (optional)
token_id = "<your-token-id>"
token_secret = "<your-token-secret>"
```

`resolve_url` is optional — defaults to `url` when absent. Use it when your
BookStack instance is behind an OAuth reverse proxy and the public URL differs
from the internal API endpoint. The resolve URL is used for web URL resolution
(`pages resolve-url`) and attachment references.

### CLI setup (recommended)

```bash
bookstack auth
# If behind an OAuth proxy with different public URL:
bookstack auth --resolve-url https://wiki.public.example.com
```

Prompts for URL, token ID, and secret. Saves to `~/.config/bookstack-cli/config.toml`.

### Environment variables (override file)

```bash
export BOOKSTACK_URL=http://10.0.0.1:8080
export BOOKSTACK_RESOLVE_URL=https://wiki.example.com
export BOOKSTACK_TOKEN_ID=<your-token-id>
export BOOKSTACK_TOKEN_SECRET=<your-token-secret>
```

Env vars take precedence over the config file.
