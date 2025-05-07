import requests
import csv
from datetime import datetime, timedelta

API_KEY = "INSERT YOUR KEY"
API_HOST = "aerodatabox.p.rapidapi.com"
IATA_CODE = "POZ" # AIRPORT CODE

headers = {
    "x-rapidapi-host": API_HOST,
    "x-rapidapi-key": API_KEY
}

def fetch_flights(start_time_utc):
    url = f"https://{API_HOST}/flights/airports/iata/{IATA_CODE}"
    offset_minutes = int((start_time_utc - datetime.utcnow()).total_seconds() // 60)
    query = {
        "offsetMinutes": str(offset_minutes), #7 DAYS IS THE LIMIT
        "durationMinutes": "720",  # 12H IS THE LIMIT
        "withLeg": "true",
        "direction": "Both",
        "withCancelled": "true",
        "withCodeshared": "true",
        "withCargo": "true",
        "withPrivate": "true",
        "withLocation": "false"
    }
    response = requests.get(url, headers=headers, params=query)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Błąd {response.status_code}: {response.text}")
        return {}

def extract_time_block(time_block):
    if not time_block:
        return ["", ""]
    return [time_block.get("utc", ""), time_block.get("local", "")]


def process_flight(flight, direction):
    result = {
        "direction": direction,
        "flight_number": flight.get("number", ""),
        "call_sign": flight.get("callSign", ""),
        "status": flight.get("status", ""),
        "codeshare_status": flight.get("codeshareStatus", ""),
        "is_cargo": flight.get("isCargo", ""),
        "airline_name": flight.get("airline", {}).get("name", ""),
        "airline_iata": flight.get("airline", {}).get("iata", ""),
        "airline_icao": flight.get("airline", {}).get("icao", ""),
        "aircraft_reg": flight.get("aircraft", {}).get("reg", ""),
        "aircraft_modeS": flight.get("aircraft", {}).get("modeS", ""),
        "aircraft_model": flight.get("aircraft", {}).get("model", ""),
        "aircraft_image_url": flight.get("aircraft", {}).get("image", {}).get("url", ""),
        "aircraft_image_web_url": flight.get("aircraft", {}).get("image", {}).get("webUrl", ""),
        "aircraft_image_author": flight.get("aircraft", {}).get("image", {}).get("author", ""),
        "aircraft_image_title": flight.get("aircraft", {}).get("image", {}).get("title", ""),
        "aircraft_image_description": flight.get("aircraft", {}).get("image", {}).get("description", ""),
        "aircraft_image_license": flight.get("aircraft", {}).get("image", {}).get("license", ""),
        "aircraft_image_html_attributions": ",".join(
            flight.get("aircraft", {}).get("image", {}).get("htmlAttributions", []))
    }

    for section in ["departure", "arrival"]:
        time_fields = flight.get(section, {})
        airport_fields = time_fields.get("airport", {})

        result.update({
            f"{section}_airport_name": airport_fields.get("name", ""),
            f"{section}_airport_iata": airport_fields.get("iata", ""),
            f"{section}_airport_icao": airport_fields.get("icao", ""),
            f"{section}_airport_local_code": airport_fields.get("localCode", ""),
            f"{section}_airport_short_name": airport_fields.get("shortName", ""),
            f"{section}_airport_municipality_name": airport_fields.get("municipalityName", ""),
            f"{section}_airport_lat": airport_fields.get("location", {}).get("lat", ""),
            f"{section}_airport_lon": airport_fields.get("location", {}).get("lon", ""),
            f"{section}_airport_country_code": airport_fields.get("countryCode", ""),
            f"{section}_airport_time_zone": airport_fields.get("timeZone", ""),

            f"{section}_scheduled_utc": time_fields.get("scheduledTime", {}).get("utc", ""),
            f"{section}_scheduled_local": time_fields.get("scheduledTime", {}).get("local", ""),
            f"{section}_revised_utc": time_fields.get("revisedTime", {}).get("utc", ""),
            f"{section}_revised_local": time_fields.get("revisedTime", {}).get("local", ""),
            f"{section}_predicted_utc": time_fields.get("predictedTime", {}).get("utc", ""),
            f"{section}_predicted_local": time_fields.get("predictedTime", {}).get("local", ""),
            f"{section}_runway_utc": time_fields.get("runwayTime", {}).get("utc", ""),
            f"{section}_runway_local": time_fields.get("runwayTime", {}).get("local", ""),

            # Additional fields for both sections
            f"{section}_terminal": time_fields.get("terminal", ""),
            f"{section}_check_in_desk": time_fields.get("checkInDesk", ""),
            f"{section}_gate": time_fields.get("gate", ""),
            f"{section}_baggage_belt": time_fields.get("baggageBelt", ""),
            f"{section}_runway": time_fields.get("runway", ""),
            f"{section}_quality": ",".join(time_fields.get("quality", []))
        })

    return result


csv_columns = [
    "direction", "flight_number", "call_sign", "status", "codeshare_status", "is_cargo",
    "airline_name", "airline_iata", "airline_icao",
    "aircraft_reg", "aircraft_modeS", "aircraft_model",
    "aircraft_image_url", "aircraft_image_web_url", "aircraft_image_author", "aircraft_image_title",
    "aircraft_image_description", "aircraft_image_license", "aircraft_image_html_attributions",

    "departure_airport_name", "departure_airport_iata", "departure_airport_icao", "departure_airport_local_code",
    "departure_airport_short_name", "departure_airport_municipality_name", "departure_airport_lat",
    "departure_airport_lon", "departure_airport_country_code", "departure_airport_time_zone",
    "departure_scheduled_utc", "departure_scheduled_local", "departure_revised_utc", "departure_revised_local",
    "departure_predicted_utc", "departure_predicted_local", "departure_runway_utc", "departure_runway_local",
    "departure_terminal", "departure_check_in_desk", "departure_gate", "departure_baggage_belt", "departure_runway",
    "departure_quality",

    "arrival_airport_name", "arrival_airport_iata", "arrival_airport_icao", "arrival_airport_local_code",
    "arrival_airport_short_name", "arrival_airport_municipality_name", "arrival_airport_lat",
    "arrival_airport_lon", "arrival_airport_country_code", "arrival_airport_time_zone",
    "arrival_scheduled_utc", "arrival_scheduled_local", "arrival_revised_utc", "arrival_revised_local",
    "arrival_predicted_utc", "arrival_predicted_local", "arrival_runway_utc", "arrival_runway_local",
    "arrival_terminal", "arrival_check_in_desk", "arrival_gate", "arrival_baggage_belt", "arrival_runway",
    "arrival_quality"
]

with open("flights_poz_May_7_23_27_last_7_days.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=csv_columns)
    writer.writeheader()

    now = datetime.utcnow()
    start = now - timedelta(days=7)

    while start < now:
        print(f"Pobieranie danych od: {start.isoformat()} UTC")
        data = fetch_flights(start)

        for flight in data.get("arrivals", []):
            writer.writerow(process_flight(flight, "arrival"))

        for flight in data.get("departures", []):
            writer.writerow(process_flight(flight, "departure"))

        start += timedelta(hours=12)

print("Loaded!")
