from airport_map import airport_map
import pandas as pd
import os
from datetime import datetime
from db import SessionLocal
from models import Airline, Airport, Airplane, Flight


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        params = {**kwargs}
        if defaults:
            params.update(defaults)
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance


def get_airport_if_known(session, data):
    """
    Only create airport if IATA code exists and is valid.
    """
    iata = data.get("airport_iata")
    if pd.isna(iata) or not iata.strip():
        return None

    return get_or_create(
        session,
        Airport,
        airport_name=data.get("airport_name"),
        airport_iata=iata,
        aiport_icao=data.get("airport_icao"),
        timezone=data.get("timezone")
    )


def populate_from_csv(session, csv_path):
    df = pd.read_csv(csv_path)
    airport_code = os.path.basename(csv_path).split('_')[1].lower()
    context_airport_data = airport_map.get(airport_code)

    if not context_airport_data:
        raise ValueError(
            f"No airport mapping found for code '{airport_code}' in file '{csv_path}'.")

    for _, row in df.iterrows():
        direction = str(row['direction']).strip().lower()

        # Airline and Airplane
        airline = get_or_create(session, Airline,
                                airline_name=row['airline_name'],
                                airline_iata=row['airline_iata'],
                                airline_icao=row['airline_icao'])

        airplane = get_or_create(session, Airplane,
                                 aircraft_model=row['aircraft_model'],
                                 aircraft_reg=row['aircraft_reg'])

        # Airports
        if direction == 'departure':
            dep_airport = get_or_create(
                session, Airport, **context_airport_data)

            arr_airport_data = {
                'airport_name': row['arrival_airport_name'],
                'airport_iata': row['arrival_airport_iata'],
                'airport_icao': row['arrival_airport_icao'],
                'timezone': row['arrival_airport_time_zone']
            }
            arr_airport = get_airport_if_known(session, arr_airport_data)

        elif direction == 'arrival':
            arr_airport = get_or_create(
                session, Airport, **context_airport_data)

            dep_airport_data = {
                'airport_name': row['departure_airport_name'],
                'airport_iata': row['departure_airport_iata'],
                'airport_icao': row['departure_airport_icao'],
                'timezone': row['departure_airport_time_zone']
            }
            dep_airport = get_airport_if_known(session, dep_airport_data)

        else:
            print(f"Unknown direction: {direction}, skipping row.")
            continue

        def parse_dt(val):
            try:
                return datetime.fromisoformat(val) if pd.notna(val) else None
            except Exception:
                return None

        dep_utc = parse_dt(row.get('departure_scheduled_utc'))
        arr_utc = parse_dt(row.get('arrival_scheduled_utc'))

        flight = Flight(
            flight_number=row['flight_number'],
            call_sign=row['call_sign'],
            arline_id=airline.id,
            airplane_id=airplane.id,
            dep_airport_id=dep_airport.id if dep_airport else None,
            arr_airport_id=arr_airport.id if arr_airport else None,
            dep_date_time_UTC=dep_utc,
            arr_date_time_UTC=arr_utc
        )
        session.add(flight)

    session.commit()


if __name__ == "__main__":
    session = SessionLocal()
    # Replace with your actual file
    populate_from_csv(
        session, "csv_data/flights_krk_May_7_23_12_last_7_days.csv")
    session.close()
