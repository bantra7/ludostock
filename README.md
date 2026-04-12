# Ludostock

Projet d'application de gestion d'une collection de jeux de société.

## Backend

L'application backend est développée en FastAPI. Elle fournit l'API pour gérer les données de la collection de jeux.

## Authentification

L'authentification est assurée par un service Better Auth dédié, configuré en connexion Google uniquement. Le frontend consomme `/api/auth/*` via proxy et le backend FastAPI valide la session courante auprès de ce service avant d'autoriser les routes métier.

## Frontend

L'application frontend est développée en React. Elle offre une interface utilisateur pour interagir avec la collection de jeux.

## Running with Docker Compose

To run the frontend, auth, and backend services with Docker Compose:

1. **Prerequisites**
   - [Docker](https://docs.docker.com/get-docker/)
   - [Docker Compose](https://docs.docker.com/compose/install/)

2. **Set environment variables**
   ```bash
   export BETTER_AUTH_SECRET=replace-with-a-secret-of-at-least-32-characters
   export GOOGLE_CLIENT_ID=replace-with-your-google-client-id
   export GOOGLE_CLIENT_SECRET=replace-with-your-google-client-secret
   export AUTH_INTERNAL_SECRET=replace-with-an-internal-shared-secret
   ```

3. **Build and start the services**
   ```bash
   docker-compose up --build
   ```

4. **Access the applications**
   - Frontend: [http://localhost:80](http://localhost:80)
   - Backend API: [http://localhost:8081](http://localhost:8081)
   - Google OAuth callback in Docker mode: `http://localhost/api/auth/callback/google`

5. **Stop the services**
   Press `Ctrl+C` in the terminal where `docker-compose up` is running.

6. **Remove the containers**
   ```bash
   docker-compose down
   ```

## Running Locally

### Backend

1. **Navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Install Python dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Configure the backend environment**
   Set `AUTH_SERVICE_URL=http://localhost:3001` and the same `AUTH_INTERNAL_SECRET` as the auth service.

4. **Run the backend application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
   ```

5. **Access the backend API**
   The backend will be accessible at [http://localhost:8081](http://localhost:8081).

### Auth

1. **Navigate to the auth directory**
   ```bash
   cd auth
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Create an environment file from `auth/.env.example`**
   Set `BETTER_AUTH_URL=http://localhost:5173` for local Vite development and configure your Google client ID and secret.

4. **Run the auth service**
   ```bash
   npm run dev
   ```

5. **Google OAuth callback for local Vite development**
   `http://localhost:5173/api/auth/callback/google`

### Frontend

1. **Navigate to the frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Run the frontend application**
   ```bash
   npm run dev
   ```

4. **Access the frontend**
   The frontend will be accessible at [http://localhost:5173](http://localhost:5173).

## Deploy on GCP

The repository now includes a [cloudbuild.yaml](/c:/Users/renau/projects/ludostock/cloudbuild.yaml) file that:

- builds the `backend`, `frontend`, and `auth` container images;
- pushes them to Artifact Registry;
- deploys the three images as three distinct Cloud Run services;
- wires the frontend proxy to the backend and auth Cloud Run URLs.

The public production origin is `https://ludostock.com`. In that setup, point the domain to the `ludostock-frontend` service only:

- `https://ludostock.com` serves the React frontend;
- `https://ludostock.com/api/*` is proxied by the frontend Nginx container to the FastAPI backend;
- `https://ludostock.com/api/auth/*` is proxied by the frontend Nginx container to the Better Auth service.

Because the frontend proxies `/api` and `/api/auth` directly to the backend and auth Cloud Run service URLs, the current deployment expects those Cloud Run services to allow unauthenticated access. If they stay private, the frontend root URL or proxied API calls can fail with `403 Forbidden`.

### Expected GCP resources

- an Artifact Registry Docker repository, for example `cloud-run-source-deploy`;
- a Cloud Storage bucket containing the SQLite seed file, for example `ludostock-data/ludostock.db`;
- three Cloud Run services:
  - `ludostock-frontend`
  - `ludostock-backend`
  - `ludostock-auth`
- four Secret Manager secrets:
  - `better-auth-secret`
  - `google-client-id`
  - `google-client-secret`
  - `auth-internal-secret`

### Required IAM for the build identity

The identity used by Cloud Build must be able to push images to Artifact Registry before the Cloud Run deployment step can start.

At minimum, grant the build service account one of these roles on the project or on the `cloud-run-source-deploy` Artifact Registry repository:

- `roles/artifactregistry.writer`
- or a broader role that already includes `artifactregistry.repositories.uploadArtifacts`

Recent Google Cloud projects can run builds with the Compute Engine default service account instead of the legacy Cloud Build service account, so verify which principal your trigger is using before granting access.

### Required IAM for the backend runtime identity

The Cloud Run service identity used by `ludostock-backend` must be able to read and write the SQLite snapshot object in Cloud Storage. If you keep the default Compute Engine service account, grant it a role such as `roles/storage.objectAdmin` on the `ludostock-data` bucket.

### Run Cloud Build

Example:

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_REGION=europe-west1,_ARTIFACT_REPOSITORY=cloud-run-source-deploy,_IMAGE_TAG=$(git rev-parse --short HEAD),_APP_VERSION=$(cat VERSION),_SQLITE_BUCKET=ludostock-data,_SQLITE_OBJECT_PATH=ludostock.db,_PUBLIC_ORIGIN=https://ludostock.com
```

### Connect ludostock.com

After the `ludostock-frontend` Cloud Run service exists, map the apex domain to that frontend service. The backend does not need a separate public domain because the frontend container proxies `/api`.

Quick Cloud Run domain mapping:

```bash
gcloud domains list-user-verified
gcloud beta run domain-mappings create \
  --service ludostock-frontend \
  --domain ludostock.com \
  --region europe-west1
gcloud beta run domain-mappings describe \
  --domain ludostock.com \
  --region europe-west1
```

Add every DNS record returned under `resourceRecords` to the DNS zone that serves `ludostock.com`. If the domain is using Cloud DNS name servers, add them in the corresponding Cloud DNS zone; if it is still using another provider's name servers, add them there.

For Google OAuth, add this authorized redirect URI in the Google Cloud OAuth client:

```text
https://ludostock.com/api/auth/callback/google
```

Cloud Run domain mappings are a convenient shortcut. For a production-grade Google Cloud setup, Google recommends an external Application Load Balancer in front of Cloud Run.

### Important runtime note

The backend currently uses SQLite. In the provided Cloud Run deployment it writes to `/tmp/ludostock.db`, downloads the latest snapshot from GCS at startup, and uploads a fresh snapshot back to GCS after each write commit. This makes the file durable across restarts, but it is still a serialized single-writer design and remains less robust than a real managed database for long-term production scale.
