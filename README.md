# Week 7 Project: Space Launches

## What it does

A data pipeline that fetches upcoming rocket launch data from the Space Launches API, validates and transforms it, then stores the raw JSON response in Azure Blob Storage and inserts cleaned structured records into a Postgres database. It runs automatically every morning at 6am as a scheduled Azure Container App Job.

## Architecture

```text
┌──────────────────────┐
│  Space Launches API  │
│  (10 launches/run)   │
└──────────┬───────────┘
           │ fetch
           ▼
┌──────────────────────┐
│  Pydantic Validation │
│  (skip bad records)  │
└──────────┬───────────┘
           │ validate
           ▼
┌──────────────────────┐
│  Pandas Transform    │
│  (clean & flatten)   │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐ ┌──────────────────┐
│  Blob   │ │    Postgres      │
│ Storage │ │ rocket_launches  │
│  (raw)  │ │ launch_providers │
└─────────┘ └──────────────────┘
```

> Runs daily at 6am as Azure Container App Job

## Run locally

```bash
# 1. Populate .env from Azure Key Vault
cp .env.example .env
echo "POSTGRES_URL=$(az keyvault secret show --vault-name kv-hyf-data --name postgres-url --query value -o tsv)" >> .env
echo "AZURE_STORAGE_CONNECTION_STRING=$(az keyvault secret show --vault-name kv-hyf-data --name storage-connection-string --query value -o tsv)" >> .env
# Set your personal schema (replace alice with your GitHub handle):
echo "DB_SCHEMA=dev_alice" >> .env

# 2. Install dependencies
uv sync

# 3. Run directly (without Docker)
uv run python -m src.pipeline

# 4. Or build and run with Docker
docker build -t hannahwn-pipeline .
docker run --env-file .env hannahwn-pipeline

# 5. Check lint errors
uv run ruff check src/
uv run ruff format --check src/
```

## Run tests

```bash
uv run pytest tests/ -v
```

## Deploy to Azure

```bash
# Build for linux/amd64 (required by Azure Container Apps) and push to ACR
docker build --platform linux/amd64 -t hyfregistry.azurecr.io/hannahwn-pipeline:latest .
docker push hyfregistry.azurecr.io/hannahwn-pipeline:latest

# Create Container App Job (runs daily at 06:00 UTC)
az containerapp job create \
  --name hannahwn-pipeline-job \
  --resource-group rg-hyf-data \
  --environment env-hyf-data \
  --image hyfregistry.azurecr.io/hannahwn-pipeline:latest \
  --registry-server hyfregistry.azurecr.io \
  --trigger-type Schedule \
  --cron-expression "0 6 * * *" \
  --replica-timeout 300 \
  --replica-retry-limit 0 \
  --env-vars \
    POSTGRES_URL="$(az keyvault secret show --vault-name kv-hyf-data --name postgres-url --query value -o tsv)" \
    AZURE_STORAGE_CONNECTION_STRING="$(az keyvault secret show --vault-name kv-hyf-data --name storage-connection-string --query value -o tsv)" \
    DB_SCHEMA=dev_hannahwn \
    LOG_LEVEL=INFO

# Trigger a manual run for testing (without waiting for the schedule)
az containerapp job start --name hannahwn-pipeline-job --resource-group rg-hyf-data
```

## Enable ACR push from CI (optional)

The `push-to-acr` job in `.github/workflows/ci.yml` is commented out by default.
To enable it, add two secrets in your repo's **Settings → Secrets and variables → Actions**:

| Secret name    | Value                                 |
| -------------- | ------------------------------------- |
| `ACR_USERNAME` | `hyfregistry`                         |
| `ACR_PASSWORD` | Ask your teacher for the ACR password |

Then uncomment the `push-to-acr` job in `ci.yml`. Every push to `main` will build
and push the image automatically.

## Install psql

`psql` is the Postgres command-line client used to verify results. Install it once:

**macOS**

```bash
brew install libpq
echo 'export PATH="/opt/homebrew/opt/libpq/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Linux (Debian/Ubuntu)**

```bash
sudo apt-get install -y postgresql-client
```

**Windows**
Download and run the installer from [postgresql.org/download/windows](https://www.postgresql.org/download/windows/). The installer includes `psql`. After installing, open a new terminal and verify with `psql --version`.

## Verify results

```bash
# Check job execution
az containerapp job execution list --name hannahwn-pipeline-job --resource-group rg-hyf-data --output table

# Check Postgres
psql "$POSTGRES_URL" -c "SELECT COUNT(*) FROM dev_hannahwn.rocket_launches;"

# Check Blob Storage
az storage blob list --account-name hyfstoragedev --container-name raw --prefix pipeline/ --output table
```

## Clean up

```bash
az containerapp job delete --name hannahwn-pipeline-job --resource-group rg-hyf-data --yes
```