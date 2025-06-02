import os
import pytest # For potential fixtures later, not strictly used in this basic setup
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Adjust imports to match your project structure if necessary
from backend.app.main import app, get_db
from backend.app.database import Base # SQLALCHEMY_DATABASE_URL is prod, not needed here
from backend.app import models # To access models like BoardGame, Label, and game_labels table
from backend.app import schemas # For request/response validation if needed directly in tests

# --- Test Database Setup ---
TEST_SQLALCHEMY_DATABASE_URL = "duckdb:///./test_boardgames.db"
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables in the test database
# This should run once before any tests. If using pytest, a session-scoped fixture is ideal.
# For this script, it runs when the module is first imported.
Base.metadata.create_all(bind=engine)

# --- Dependency Override ---
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# --- Database Cleanup Function ---
def cleanup_db():
    """Cleans all data from relevant tables before each test."""
    db = TestingSessionLocal()
    try:
        # Order of deletion matters due to foreign key constraints.
        # Clear the association table first.
        db.execute(models.game_labels.delete()) # Assuming game_labels is a Table object
        db.query(models.BoardGame).delete()
        db.query(models.Label).delete()
        db.commit()
    finally:
        db.close()

# --- Test Cases ---

# == Label Tests ==

def test_create_label():
    cleanup_db()
    response = client.post("/labels/", json={"name": "Strategy"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Strategy"
    assert "id" in data

def test_create_label_duplicate_name():
    cleanup_db()
    client.post("/labels/", json={"name": "Strategy"}) # Create first label
    response = client.post("/labels/", json={"name": "Strategy"}) # Attempt duplicate
    assert response.status_code == 400
    assert response.json()["detail"] == "Label with this name already exists"

def test_get_labels():
    cleanup_db()
    client.post("/labels/", json={"name": "Family"})
    client.post("/labels/", json={"name": "Abstract"})
    response = client.get("/labels/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Family"
    assert data[1]["name"] == "Abstract"

def test_get_label_by_id():
    cleanup_db()
    label_response = client.post("/labels/", json={"name": "Worker Placement"})
    label_id = label_response.json()["id"]
    response = client.get(f"/labels/{label_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Worker Placement"
    assert data["id"] == label_id

def test_get_label_not_found():
    cleanup_db()
    response = client.get("/labels/99999")
    assert response.status_code == 404

def test_update_label():
    cleanup_db()
    label_response = client.post("/labels/", json={"name": "Cooperative"})
    label_id = label_response.json()["id"]
    response = client.put(f"/labels/{label_id}", json={"name": "Co-op"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Co-op"
    # Verify by fetching again
    get_response = client.get(f"/labels/{label_id}")
    assert get_response.json()["name"] == "Co-op"

def test_update_label_not_found():
    cleanup_db()
    response = client.put("/labels/99999", json={"name": "Doesnt Exist"})
    assert response.status_code == 404

def test_delete_label():
    cleanup_db()
    label_response = client.post("/labels/", json={"name": "Legacy"})
    label_id = label_response.json()["id"]
    response = client.delete(f"/labels/{label_id}")
    assert response.status_code == 200
    # Verify by trying to get it again
    get_response = client.get(f"/labels/{label_id}")
    assert get_response.status_code == 404

def test_delete_label_not_found():
    cleanup_db()
    response = client.delete("/labels/99999")
    assert response.status_code == 404

# == BoardGame Tests ==

def test_create_board_game_no_labels():
    cleanup_db()
    game_data = {
        "name": "Terraforming Mars", "editor_name": "FryxGames",
        "num_players_min": 1, "num_players_max": 5, "age_min": 12,
        "time_duration_mean": 120
    }
    response = client.post("/boardgames/", json=game_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Terraforming Mars"
    assert data["editor_name"] == "FryxGames"
    assert len(data["labels"]) == 0

def test_create_board_game_with_new_labels():
    cleanup_db()
    game_data = {
        "name": "Wingspan", "editor_name": "Stonemaier Games",
        "num_players_min": 1, "num_players_max": 5, "age_min": 10,
        "time_duration_mean": 60, "labels": ["Engine Building", "Animals"]
    }
    response = client.post("/boardgames/", json=game_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Wingspan"
    assert len(data["labels"]) == 2
    label_names = sorted([l["name"] for l in data["labels"]])
    assert label_names == ["Animals", "Engine Building"]
    # Check if labels were actually created in DB
    labels_response = client.get("/labels/")
    assert len(labels_response.json()) == 2


def test_create_board_game_with_existing_labels():
    cleanup_db()
    # Create labels first
    label1_resp = client.post("/labels/", json={"name": "Card Game"})
    label2_resp = client.post("/labels/", json={"name": "Set Collection"})
    assert label1_resp.status_code == 200
    assert label2_resp.status_code == 200

    game_data = {
        "name": "7 Wonders", "editor_name": "Repos Production",
        "num_players_min": 2, "num_players_max": 7, "age_min": 10,
        "time_duration_mean": 30, "labels": ["Card Game", "Set Collection"]
    }
    response = client.post("/boardgames/", json=game_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "7 Wonders"
    assert len(data["labels"]) == 2
    label_ids_in_game = sorted([l["id"] for l in data["labels"]])
    expected_label_ids = sorted([label1_resp.json()["id"], label2_resp.json()["id"]])
    assert label_ids_in_game == expected_label_ids

def test_get_board_games():
    cleanup_db()
    client.post("/boardgames/", json={
        "name": "Gloomhaven", "editor_name": "Cephalofair", "num_players_min": 1,
        "num_players_max": 4, "age_min": 14, "time_duration_mean": 90, "labels": ["Campaign"]
    })
    client.post("/boardgames/", json={
        "name": "Azul", "editor_name": "Next Move", "num_players_min": 2,
        "num_players_max": 4, "age_min": 8, "time_duration_mean": 40, "labels": ["Abstract"]
    })
    response = client.get("/boardgames/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Gloomhaven"
    assert data[1]["name"] == "Azul"

def test_get_board_game_by_id():
    cleanup_db()
    game_resp = client.post("/boardgames/", json={
        "name": "Pandemic", "editor_name": "Z-Man Games", "num_players_min": 2,
        "num_players_max": 4, "age_min": 8, "time_duration_mean": 45, "labels": ["Cooperative"]
    })
    game_id = game_resp.json()["id"]
    response = client.get(f"/boardgames/{game_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Pandemic"
    assert len(data["labels"]) == 1
    assert data["labels"][0]["name"] == "Cooperative"

def test_get_board_game_not_found():
    cleanup_db()
    response = client.get("/boardgames/99999")
    assert response.status_code == 404

def test_update_board_game_scalar_fields():
    cleanup_db()
    game_resp = client.post("/boardgames/", json={
        "name": "Scythe", "editor_name": "Stonemaier", "num_players_min": 1,
        "num_players_max": 5, "age_min": 14, "time_duration_mean": 115
    })
    game_id = game_resp.json()["id"]
    update_payload = {"name": "Scythe: Epic Edition", "editor_name": "Stonemaier Games"}
    response = client.put(f"/boardgames/{game_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Scythe: Epic Edition"
    assert data["editor_name"] == "Stonemaier Games"
    # Verify original fields not in payload are unchanged
    assert data["num_players_min"] == 1

def test_update_board_game_add_labels():
    cleanup_db()
    game_resp = client.post("/boardgames/", json={
        "name": "Carcassonne", "editor_name": "Hans im Glück", "num_players_min": 2,
        "num_players_max": 5, "age_min": 7, "time_duration_mean": 35, "labels": []
    })
    game_id = game_resp.json()["id"]
    assert len(game_resp.json()["labels"]) == 0
    update_payload = {"labels": ["Tile Placement", "Medieval"]}
    response = client.put(f"/boardgames/{game_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["labels"]) == 2
    label_names = sorted([l["name"] for l in data["labels"]])
    assert label_names == ["Medieval", "Tile Placement"]

def test_update_board_game_change_labels():
    cleanup_db()
    client.post("/labels/", json={"name": "Area Control"}) # Ensure "Area Control" exists
    game_resp = client.post("/boardgames/", json={
        "name": "Root", "editor_name": "Leder Games", "num_players_min": 2,
        "num_players_max": 4, "age_min": 10, "time_duration_mean": 75, "labels": ["Wargame"]
    })
    game_id = game_resp.json()["id"]
    assert game_resp.json()["labels"][0]["name"] == "Wargame"
    update_payload = {"labels": ["Area Control", "Asymmetric"]} # "Asymmetric" is new
    response = client.put(f"/boardgames/{game_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["labels"]) == 2
    label_names = sorted([l["name"] for l in data["labels"]])
    assert label_names == ["Area Control", "Asymmetric"]

def test_update_board_game_remove_labels():
    cleanup_db()
    game_resp = client.post("/boardgames/", json={
        "name": "Ticket to Ride", "editor_name": "Days of Wonder", "num_players_min": 2,
        "num_players_max": 5, "age_min": 8, "time_duration_mean": 60, "labels": ["Family", "Trains"]
    })
    game_id = game_resp.json()["id"]
    assert len(game_resp.json()["labels"]) == 2
    update_payload = {"labels": []} # Remove all labels
    response = client.put(f"/boardgames/{game_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["labels"]) == 0

def test_update_board_game_no_label_change_in_payload():
    cleanup_db()
    game_resp = client.post("/boardgames/", json={
        "name": "Everdell", "editor_name": "Starling Games", "num_players_min": 1,
        "num_players_max": 4, "age_min": 10, "time_duration_mean": 60, "labels": ["City Building"]
    })
    game_id = game_resp.json()["id"]
    original_labels = game_resp.json()["labels"]

    update_payload = {"name": "Everdell: Collector's Edition"} # No 'labels' key in payload
    response = client.put(f"/boardgames/{game_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Everdell: Collector's Edition"
    assert len(data["labels"]) == 1 # Labels should be unchanged
    assert data["labels"][0]["name"] == original_labels[0]["name"]


def test_update_board_game_not_found():
    cleanup_db()
    response = client.put("/boardgames/99999", json={"name": "Non Existent"})
    assert response.status_code == 404

def test_delete_board_game():
    cleanup_db()
    game_resp = client.post("/boardgames/", json={
        "name": "Patchwork", "editor_name": "Lookout Games", "num_players_min": 2,
        "num_players_max": 2, "age_min": 8, "time_duration_mean": 30
    })
    game_id = game_resp.json()["id"]
    response = client.delete(f"/boardgames/{game_id}")
    assert response.status_code == 200
    # Verify by trying to get it again
    get_response = client.get(f"/boardgames/{game_id}")
    assert get_response.status_code == 404

def test_delete_board_game_not_found():
    cleanup_db()
    response = client.delete("/boardgames/99999")
    assert response.status_code == 404

# Consider adding a fixture to clean up the test_boardgames.db file after all tests run
# For example, using pytest:
# @pytest.fixture(scope="session", autouse=True)
# def cleanup_test_db_file():
#     yield # Let all tests run
#     # Teardown: remove the test DB file
#     if os.path.exists(TEST_SQLALCHEMY_DATABASE_URL.replace("duckdb:///", "")):
#         os.remove(TEST_SQLALCHEMY_DATABASE_URL.replace("duckdb:///", ""))

# For now, manual cleanup might be needed if the file is disk-based.
# If TEST_SQLALCHEMY_DATABASE_URL was "duckdb:///:memory:", no file cleanup is needed.
# However, :memory: db might be cleared between TestClient calls or need careful session management.
# Using a file-based one like "./test_boardgames.db" is often more straightforward for TestClient
# as long as tables are created once and data is cleaned per test.
