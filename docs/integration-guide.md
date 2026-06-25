# Integration Guide

Reference from [BookStack Hacking Guide](https://www.bookstackapp.com/docs/admin/hacking-bookstack/).

## Custom HTML/CSS Injection

### Custom HTML Head Content
Admin → Settings → "Custom HTML head content"

Injected just before `</head>` on every page. Use for:
- Analytics snippets (Plausible, Umami, Matomo)
- Custom JavaScript
- Additional stylesheets
- Meta tags

```html
<!-- Example: custom font -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600" rel="stylesheet">
```

### Custom Body Start/End
Available in newer BookStack versions:
- **Body start**: injected after `<body>`
- **Body end**: injected before `</body>`

### Custom Stylesheet
Admin → Settings → "Custom stylesheet"

Raw CSS, no `<style>` tags needed:
```css
.shelf-grid .book-card { border-radius: 12px; }
.page-content { font-size: 16px; line-height: 1.7; }
```

### App-Level Override (Advanced)
Place custom Blade templates in the `resources/` override path
for deeper UI customization. Requires filesystem access to the server.

## Webhooks & Events

**No native outgoing webhooks** as of BookStack v24.

Workarounds:
1. **Polling**: Use CLI `GET /api/pages` on interval, diff `updated_at`
2. **Community packages**: Some third-party packages add webhook support
3. **Custom middleware**: Hook Laravel events (`PageCreated`, `PageUpdated`,
   `PageDeleted`) with custom code on the server

Internal Laravel events available for server-side hooks:
- `BookStack\Actions\ActivityType\PAGE_CREATE`
- `BookStack\Actions\ActivityType\PAGE_UPDATE`
- `BookStack\Actions\ActivityType\PAGE_DELETE`
- Similar for books, chapters, shelves

## Security & Permissions

- API tokens inherit user role permissions — create dedicated service accounts
- Content visibility matches UI: users only see what their role permits
- No API-only permission level — API access is all-or-nothing per user

## Multi-Tenancy

BookStack is single-tenant by default. Instance per team/org if isolation needed.

## Schema Export

- OpenAPI JSON spec: `<bookstack_url>/api/docs.json`
- Interactive API docs: `<bookstack_url>/api/docs`
- No full system schema dump tool built-in

## Recommended Setup for Automation

1. Create a dedicated "api-bot" user account
2. Assign minimal required role
3. Generate API token for that user
4. Store in environment variables
5. Use HTTPS in production
