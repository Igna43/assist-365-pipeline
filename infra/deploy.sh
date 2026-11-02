#!/usr/bin/env bash
# Deploy the daily pipeline. The API token is read from .env and injected into
# the Cloud Run job. Secret Manager is not enabled on this project, and this
# account cannot enable APIs (serviceusage.services.enable is denied).
set -euo pipefail
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo ".env is missing" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

PROJECT="${GCP_PROJECT:-a365-de-imangini}"
REGION="${GCP_REGION:-us-central1}"
BUCKET="${GCS_BUCKET:-a365-de-imangini-raw}"
JOB="a365-pipeline"
SA_NAME="a365-pipeline"
SA="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"

gcloud config set project "$PROJECT"

if ! gcloud iam service-accounts describe "$SA" --project="$PROJECT" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="Assist-365 pipeline" \
    --project="$PROJECT"
fi

# This account cannot call projects.setIamPolicy, so the dedicated SA cannot
# receive BigQuery roles. The Compute Engine default service account already
# has roles/editor on the project, which covers BigQuery, GCS, and Cloud Run.
RUNTIME_SA="152941963971-compute@developer.gserviceaccount.com"
SCHEDULER_AGENT="service-${PROJECT_NUMBER:-152941963971}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"

gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${SA}" \
  --role="roles/storage.objectAdmin" \
  --project="$PROJECT"

gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --project="$PROJECT" \
  --member="serviceAccount:${SCHEDULER_AGENT}" \
  --role="roles/iam.serviceAccountTokenCreator"

gcloud run jobs deploy "$JOB" \
  --source . \
  --region "$REGION" \
  --project "$PROJECT" \
  --service-account "$RUNTIME_SA" \
  --memory 2Gi \
  --cpu 1 \
  --task-timeout 60m \
  --max-retries 1 \
  --set-env-vars "GCP_PROJECT=${PROJECT},GCS_BUCKET=${BUCKET},BQ_LOCATION=${BQ_LOCATION:-US},A365_API_BASE=${A365_API_BASE},A365_API_TOKEN=${A365_API_TOKEN}"

gcloud run jobs add-iam-policy-binding "$JOB" \
  --region="$REGION" \
  --project="$PROJECT" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/run.invoker"

SCHEDULER="a365-pipeline-daily"
URI="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT}/jobs/${JOB}:run"

if gcloud scheduler jobs describe "$SCHEDULER" --location="$REGION" --project="$PROJECT" >/dev/null 2>&1; then
  gcloud scheduler jobs update http "$SCHEDULER" \
    --location="$REGION" \
    --project="$PROJECT" \
    --schedule="0 8 * * *" \
    --time-zone="America/Bogota" \
    --uri="$URI" \
    --http-method=POST \
    --oauth-service-account-email="$RUNTIME_SA"
else
  gcloud scheduler jobs create http "$SCHEDULER" \
    --location="$REGION" \
    --project="$PROJECT" \
    --schedule="0 8 * * *" \
    --time-zone="America/Bogota" \
    --uri="$URI" \
    --http-method=POST \
    --oauth-service-account-email="$RUNTIME_SA"
fi

echo "deployed ${JOB} as ${RUNTIME_SA} and ${SCHEDULER} in ${REGION}"
