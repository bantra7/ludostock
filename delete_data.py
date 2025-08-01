import requests

BASE_URL = "https://ludostock-backend-1015299081216.europe-west1.run.app/api"
AUTHORS_ENDPOINT = f"{BASE_URL}/authors/"
EDITORS_ENDPOINT = f"{BASE_URL}/editors/"
ARTISTS_ENDPOINT = f"{BASE_URL}/artists/"
DISTRIBUTORS_ENDPOINT = f"{BASE_URL}/distributors/"
GAMES_ENDPOINT = f"{BASE_URL}/games/"

def delete_all_records(endpoint):
    # Fetch all records
    response = requests.get(endpoint)
    response.raise_for_status()
    records = response.json()
    
    print(f"Found {len(records)} records in {endpoint}")

    for record in records:
        record_id = record.get("id")
        if record_id:
            del_response = requests.delete(f"{endpoint}{record_id}/")
            if del_response.status_code == 204:
                print(f"✅ Deleted {endpoint} ID: {record_id}")
            else:
                print(f"❌ Failed to delete {endpoint} ID: {record_id}, "
                      f"status: {del_response.status_code}, "
                      f"response: {del_response.text}")

def main():
    delete_all_records(AUTHORS_ENDPOINT)
    delete_all_records(EDITORS_ENDPOINT)
    delete_all_records(ARTISTS_ENDPOINT)
    delete_all_records(DISTRIBUTORS_ENDPOINT)
    delete_all_records(GAMES_ENDPOINT)

if __name__ == "__main__":
    main()