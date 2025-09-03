# Nexis

## Quick Start (Windows PowerShell)

1) Backend env (optional - safe defaults used if unset)

Create `.env` in project root:

```
MONGO_URL=mongodb://127.0.0.1:27017
REDDIT_CLIENT_ID=
REDDIT_SECRET=
NEWSAPI_KEY=
YOUTUBE_API_KEY=
USE_MOCK_TWITTER=true
USE_MOCK_FACEBOOK=true
```

2) Install backend deps (already pinned for Py3.12/Windows):

```
python -m pip install -r backend/requirements.txt
```

3) Start backend:

```
python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000
```

4) Frontend setup:

```
cd frontend
yarn install
yarn dev
```

Open http://127.0.0.1:3000

## Supervisor on PowerShell

PowerShell does not support `&&`. Use `;` as separator:

```
cd S:\nexis; supervisord -c supervisord.conf
```

Common commands:

```
supervisorctl status
supervisorctl stop all
supervisorctl start all
```

## Notes
- Backend runs without API keys using safe fallbacks. Provide keys for real integrations.
- Transformers is optional on Windows (enable Long Paths to install).