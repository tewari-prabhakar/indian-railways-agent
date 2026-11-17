import os
import requests
from dotenv import load_dotenv

# Load your keys from the hidden .env file
load_dotenv()

def get_trains_between_stations(from_station_code: str, to_station_code: str, date_of_journey: str) -> dict:
    """
    Fetches trains running between two Indian Railway stations on a given date.

    Args:
        from_station_code: The 2-to-4 letter source station code in uppercase (e.g., 'CNB' for Kanpur Central).
        to_station_code: The 2-to-4 letter destination station code in uppercase (e.g., 'NDLS' for New Delhi).
        date_of_journey: Travel date strictly in DD-MM-YYYY format (e.g., '2026-11-20').

    Returns:
        A dictionary containing the list of matching trains or an error message.
    """
    print(f"   [Tool] Searching IRCTC API: {from_station_code} -> {to_station_code} on {date_of_journey}...")
    
    url = "https://irctc1.p.rapidapi.com/api/v3/trainBetweenStations"

    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": os.getenv("RAPIDAPI_HOST", "irctc1.p.rapidapi.com")
    }

    querystring = {
        "fromStationCode": from_station_code.upper().strip(),
        "toStationCode": to_station_code.upper().strip(),
        "dateOfJourney": date_of_journey.strip()
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Trim down the raw API response so we only send clean, useful info back to the AI
        trains = data.get("data", [])
        if not trains:
            return {"status": "no_trains_found", "raw_message": data.get("message", "No trains returned.")}

        clean_trains = []
        for t in trains:
            clean_trains.append({
                "train_number": t.get("train_number"),
                "train_name": t.get("train_name"),
                "from": t.get("from_std"),          # Departure time
                "to": t.get("to_sta"),              # Arrival time
                "duration": t.get("duration"),
                "running_days": t.get("run_days")
            })

        return {"status": "success", "total_trains": len(clean_trains), "trains": clean_trains}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# Quick test block (runs ONLY when we run tools.py directly)
if __name__ == "__main__":
    print("Testing RapidAPI connection for CNB -> NDLS on 2026-11-20...")
    result = get_trains_between_stations("CNB", "NDLS", "2026-11-20")
    print(result)