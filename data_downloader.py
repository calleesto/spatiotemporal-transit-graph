import requests
import zipfile
import io
import os

GTFS_URL = "https://ckan.multimediagdansk.pl/dataset/c24aa637-3619-4dc2-a171-a23eec8f2172/resource/30e783e4-2bec-4a7d-bb22-ee3e3b26ca96/download/gtfsgoogle.zip"

from graph_builder import GTFS_FOLDER

def fetch_latest_gtfs():
    print("downloading up-to-date GTFS data")

    try:
        response = requests.get(GTFS_URL)
        response.raise_for_status()

        print("download successful - extracting files")

        os.makedirs(GTFS_FOLDER, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(GTFS_FOLDER)

        print(f"extract successful - files located in \033[1m{GTFS_FOLDER}\033[0m")

    except requests.exceptions.RequestException as e:
        print(f"error: {e}")

if __name__ == '__main__':
    fetch_latest_gtfs()