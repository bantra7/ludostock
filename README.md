# boardgame-app
Projet d'app de gestion d'une collection de jeux de société.

## boardgame-backend
Appli Backend développée en FastAPI.

## boardgamr-frontend
Appli Fronted développée en React.


## Tips

### Mettre à jour Python après installation de librairies

```
cd Python-3.9.15/
./configure --enable-optimizations
sudo make altinstall
sudo make install
```

## Running the Frontend (React)

To run the frontend application:

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install dependencies:**
    If you haven't already, install the necessary Node.js packages.
    ```bash
    npm install
    ```

3.  **Start the development server:**
    ```bash
    npm start
    ```
    This will typically open the application in your default web browser at `http://localhost:3000`.

**Note:** Ensure the backend application is running and accessible, as the frontend relies on it for data. By default, the frontend will try to connect to the backend at `http://localhost:8000/api`.
