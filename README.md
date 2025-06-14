# boardgame-app

Projet d'application de gestion d'une collection de jeux de société.

## Backend

L'application Backend est développée en FastAPI. Elle fournit l'API pour gérer les données de la collection de jeux.

## Frontend

L'application Frontend est développée en React. Elle offre une interface utilisateur pour interagir avec la collection de jeux

## Running with Docker Compose

To run the frontend and backend applications using Docker Compose, follow these steps:

1.  **Build and start the services:**
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker images for both the frontend and backend (if they don't exist or if changes were made) and then start the containers.

2.  **Access the applications:**
    *   Frontend: Open your web browser and go to [http://localhost:3000](http://localhost:3000)
    *   Backend API: The backend will be accessible at [http://localhost:8080](http://localhost:8080)

3.  **To stop the services:**
    Press `Ctrl+C` in the terminal where `docker-compose up` is running.

4.  **To stop and remove the containers:**
    ```bash
    docker-compose down
    ```