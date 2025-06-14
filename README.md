# boardgame-app

Projet d'application de gestion d'une collection de jeux de société.

## Backend

L'application Backend est développée en FastAPI. Elle fournit l'API pour gérer les données de la collection de jeux.

## Frontend

L'application Frontend est développée en React. Elle offre une interface utilisateur pour interagir avec la collection de jeux

## Running with Docker Compose

To run the frontend and backend applications using Docker Compose, ensure you have Docker and Docker Compose installed on your system. Then, follow these steps:

1.  **Prerequisites:**
    *   [Docker](https://docs.docker.com/get-docker/)
    *   [Docker Compose](https://docs.docker.com/compose/install/)

2.  **Build and start the services:**
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker images for both the frontend and backend (if they don't exist or if changes were made) and then start the containers.

3.  **Access the applications:**
    *   Frontend: Open your web browser and go to [http://localhost:3000](http://localhost:3000)
    *   Backend API: The backend will be accessible at [http://localhost:8080](http://localhost:8080)

4.  **To stop the services:**
    Press `Ctrl+C` in the terminal where `docker-compose up` is running.

5.  **To stop and remove the containers:**
    ```bash
    docker-compose down
    ```

## Running Locally (Without Docker)

This section describes how to run the backend and frontend applications directly on your local machine without using Docker.

### Backend

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Install Python dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Run the backend application:**
    ```bash
    ./start-dev.sh
    ```
    Alternatively, you can run uvicorn directly:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
    ```

4.  **Access the backend API:**
    The backend will be accessible at [http://localhost:8080](http://localhost:8080).

### Frontend

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

3.  **Run the frontend application:**
    ```bash
    npm start
    ```

4.  **Access the frontend application:**
    The frontend will be accessible at [http://localhost:3000](http://localhost:3000).
    The application will automatically reload if you make changes to the source files.
