Here's the full local Docker testing sequence, consolidated from what's been fixed so far.

## Prerequisites (one-time setup, skip if already done)

- Docker Desktop running
- Cloud SQL Auth Proxy binary available
- `.env` file present in your project root with `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (gitignored, not built into the image)
- Authenticated with `gcloud` (`gcloud auth application-default login`)

## Step 1 — Start the Cloud SQL Auth Proxy

In its own terminal window, leave it running:

```powershell
.\cloud-sql-proxy.exe --port 5433 budgetsense-gcp-prod:australia-southeast1:budgetsense-db
```

Confirm it says it's ready to accept connections before moving on. (This is the exact region fix from earlier — `australia-southeast1`, not `us-central1`.)

## Step 2 — Quick import sanity check (fastest, catches import bugs before building anything)

In a second terminal, from `src/`:

```powershell
python -c "import main"
```

If this throws, fix it before building — no point wrapping a Docker build around a bug you can see in one second.

## Step 3 — Build the Docker image

From the repo root (wherever your `Dockerfile` lives):

```powershell
docker build -t budgetsense-app:test .
```

## Step 4 — Run the container locally

```powershell
docker run -p 8080:8080 --env-file .env -e DB_HOST=host.docker.internal -e DB_PORT=5433 budgetsense-app:test
```

Watch this terminal for `Application startup complete` with no traceback. Leave it running.

**Note:** your Cloud SQL connection uses a private IP reachable only via the VPC connector in the actually-deployed Cloud Run environment — the local container has no path to that network, so `/health`'s DB check will fail here even when the app starts correctly. That's expected, not a bug; this step confirms the app _starts_, not that it can reach the database.

## Step 5 — Confirm it's serving, in a third terminal

```powershell
curl http://localhost:8080/
```

Should return `{"service": "budgetsense-gcp", "status": "running"}`.

## Step 6 — Open the UI in a browser

```
http://localhost:8080/
```

This is where you'll actually see the formatting/UX changes — submit a test question (WATO for a quick single-topic check, the small-business question to exercise the category-heading/collapse/Next-Steps features) and visually confirm everything renders as expected before redeploying.

## Step 7 — When done testing

In the container's terminal: `Ctrl+C`
Or from another terminal:

```powershell
docker ps
docker stop <container_id>
```

---

Once everything checks out locally, the push/deploy sequence (tag → push to Artifact Registry → `gcloud run deploy`) is the same as the last few rounds — let me know if you want that repeated too, or if you're just testing locally for now without redeploying yet.
