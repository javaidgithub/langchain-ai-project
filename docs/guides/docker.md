# Docker Deployment

```bash
cp .env.example .env    # add your provider keys
docker compose up --build
# open http://localhost:8080
```

The first build takes 2–4 minutes. Subsequent starts are fast.

## Services

| Container | Image | Port |
|---|---|---|
| `backend` | python:3.12-slim | internal :8000 |
| `frontend` | nginx:1.27-alpine | host :8080 |

Nginx serves the compiled React app and proxies `/api` to the backend with buffering disabled.

## Data persistence

Conversations, the vector store and the agent workspace live in the `app-data` Docker volume.

```bash
docker compose down      # stop, keep data
docker compose down -v   # stop and delete data
```

## Production checklist

- [ ] Set `API_AUTH_TOKEN` in `.env`
- [ ] Set `ENVIRONMENT=production`
- [ ] Use HTTPS with a reverse proxy (Caddy / nginx)
- [ ] Disable buffering and set a long read timeout on `/api` paths
- [ ] Back up the `app-data` volume
