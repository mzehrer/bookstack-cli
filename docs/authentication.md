# Authentication

BookStack uses API token pairs — no OAuth, no session auth for API.

## Token Format

Every user can generate a token pair from their profile page:

```
Settings → API Tokens → Create
```

Token pair consists of:
- **Token ID** — public identifier (e.g. `ltA4dR2k6QhGxY1z`)
- **Token Secret** — secret value shown once (e.g. `AbCdeFgHiJkLmNoPqRsTuVwXyZ0123456789`)

## Request Header

```
Authorization: Token <token_id>:<token_secret>
```

Example:

```
Authorization: Token ltA4dR2k6QhGxY1z:AbCdeFgHiJkLmNoPqRsTuVwXyZ0123456789
```

The token is sent as a plaintext colon-separated pair (not Base64-encoded
Basic auth, though the format resembles it).

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
url = "https://wiki.example.com"
token_id = "ltA4dR2k6QhGxY1z"
token_secret = "AbCdeFgHiJkLmNoPqRsTuVwXyZ0123456789"
```

### CLI setup (recommended)

```bash
bookstack auth
```

Prompts for URL, token ID, and secret. Saves to `~/.config/bookstack-cli/config.toml`.

### Environment variables (override file)

```bash
export BOOKSTACK_URL=https://wiki.example.com
export BOOKSTACK_TOKEN_ID=ltA4dR2k6QhGxY1z
export BOOKSTACK_TOKEN_SECRET=AbCdeFgHiJkLmNoPqRsTuVwXyZ0123456789
```

Env vars take precedence over the config file.
