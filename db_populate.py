from airport_map import airport_map
import pandas as pd
import os
from datetime import datetime
from copy import deepcopy
from db import SessionLocal
from models import Airline, Airport, Airplane, Flight, FlightDetails


def get_or_create(session, model, defaults=None, **kwargs):
    # Filter out None or empty values from kwargs
    filtered_kwargs = {k: v for k, v in kwargs.items() if v not in [None, ""]}
    instance = session.query(model).filter_by(**filtered_kwargs).first()
    if instance:
        return instance
    else:
        params = {**filtered_kwargs}
        if defaults:
            params.update(defaults)
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance


def get_or_create_airline(session, data):
    """
    Custom get_or_create logic for Airline to handle potential duplicates.
    """
    # Prioritize unique identifiers (iata and icao) over name
    query_filters = {}
    if pd.notna(data.get('airline_iata')) and data['airline_iata'].strip():
        query_filters['airline_iata'] = data['airline_iata'].strip()
    elif pd.notna(data.get('airline_icao')) and data['airline_icao'].strip():
        query_filters['airline_icao'] = data['airline_icao'].strip()
    elif pd.notna(data.get('airline_name')) and data['airline_name'].strip():
        query_filters['airline_name'] = data['airline_name'].strip()

    if not query_filters:
        return None  # No valid data to identify the airline

    instance = session.query(Airline).filter_by(**query_filters).first()
    if instance:
        return instance

    # Create a new airline if no match is found
    return get_or_create(session, Airline,
                         airline_name=data.get('airline_name'),
                         airline_iata=data.get('airline_iata'),
                         airline_icao=data.get('airline_icao'))


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
        airport_icao=data.get("airport_icao"),
        timezone=data.get("timezone"),
        latitude=data.get('latitude'),
        longitude=data.get('longitude')
    )


def populate_from_csv(session, csv_path, additional_data_path='additional_data.xlsx'):
    df = pd.read_csv(csv_path)
    airport_code = os.path.basename(csv_path).split('_')[1].lower()
    context_airport_data = airport_map.get(airport_code)
    additional_data = pd.read_excel(additional_data_path)       # additional airport data

    if not context_airport_data:
        raise ValueError(
            f"No airport mapping found for code '{airport_code}' in file '{csv_path}'.")

    for _, row in df.iterrows():
        # Filter rows based on status
        if row['status'] not in ['Arrived', 'Departed']:
            continue

        direction = str(row['direction']).strip().lower()

        # Airline and Airplane
        airline = None
        if pd.notna(row['airline_name']) and row['airline_name'] == "Unknown/Private owner":
            print(f"Skipping row with airline name: {row['airline_name']}")
            continue

        if pd.notna(row['airline_name']) or pd.notna(row['airline_iata']) or pd.notna(row['airline_icao']):
            airline = get_or_create_airline(session, {
                'airline_name': row['airline_name'],
                'airline_iata': row['airline_iata'],
                'airline_icao': row['airline_icao']
            })

        airplane = None
        if pd.notna(row['aircraft_model']) or pd.notna(row['aircraft_reg']):
            airplane = get_or_create(session, Airplane,
                                     aircraft_model=row['aircraft_model'],
                                     aircraft_reg=row['aircraft_reg'])

        # Airports
        if direction == 'departure':
            if pd.isna(row['arrival_airport_name']) or pd.isna(row['arrival_airport_iata']) or pd.isna(row['arrival_airport_icao']):
                print(
                    f"Missing arrival airport data for row: {row['flight_number']}")
                continue

            # Merge context data dict with additional data dict
            additional_info = additional_data[additional_data['iata'] == context_airport_data['airport_iata']]

            context_airport_data_tmp = deepcopy(context_airport_data)
            additional_data_tmp = {'latitude': additional_info.iloc[0]["lat"],
                                   'longitude': additional_info.iloc[0]["long"]}

            context_airport_data_tmp.update(additional_data_tmp)

            dep_airport = get_or_create(
                session, Airport, **context_airport_data_tmp)


            arr_airport_data = {
                'airport_name': row['arrival_airport_name'],
                'airport_iata': row['arrival_airport_iata'],
                'airport_icao': row['arrival_airport_icao'],
                'timezone': row['arrival_airport_time_zone'],
                'latitude': additional_info.iloc[0]["lat"],
                'longitude': additional_info.iloc[0]["long"]
            }

            arr_airport = get_airport_if_known(session, arr_airport_data)

        elif direction == 'arrival':
            if pd.isna(row['departure_airport_name']) or pd.isna(row['departure_airport_iata']) or pd.isna(row['departure_airport_icao']):
                print(
                    f"Missing departure airport data for row: {row['flight_number']}")
                continue

            additional_info = additional_data[additional_data['iata'] == context_airport_data['airport_iata']]

            context_airport_data_tmp = deepcopy(context_airport_data)
            additional_data_tmp = {'latitude': additional_info.iloc[0]["lat"],
                                   'longitude': additional_info.iloc[0]["long"]}

            context_airport_data_tmp.update(additional_data_tmp)

            arr_airport = get_or_create(
                session, Airport, **context_airport_data_tmp)


            dep_airport_data = {
                'airport_name': row['departure_airport_name'],
                'airport_iata': row['departure_airport_iata'],
                'airport_icao': row['departure_airport_icao'],
                'timezone': row['departure_airport_time_zone'],
                'latitude': additional_info.iloc[0]["lat"],
                'longitude': additional_info.iloc[0]["long"]
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
        dep_rev_utc = parse_dt(row.get('departure_revised_utc'))
        if dep_rev_utc is None:
            dep_rev_utc = dep_utc

        arr_utc = parse_dt(row.get('arrival_scheduled_utc'))
        arr_rev_utc = parse_dt(row.get('arrival_revised_utc'))
        if arr_rev_utc is None:
            arr_rev_utc = arr_utc

        # Flight Details
        flight_details = get_or_create(session, FlightDetails,
                                       flight_number=row['flight_number'],
                                       call_sign=row['call_sign'])

        # Flight
        flight = Flight(
            status=row['status'],
            flight_details_id=flight_details.id,
            arline_id=airline.id if airline else None,
            airplane_id=airplane.id if airplane else None,
            dep_airport_id=dep_airport.id if dep_airport else None,
            arr_airport_id=arr_airport.id if arr_airport else None,
            dep_date_time_UTC=dep_utc,
            dep_rev_date_time_UTC=dep_rev_utc,
            arr_date_time_UTC=arr_utc,
            arr_rev_date_time_UTC=arr_rev_utc
        )
        session.add(flight)

    session.commit()


def main():
    session = SessionLocal()
    folder_path = "csv_data"
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            csv_path = os.path.join(folder_path, file_name)
            print(f"Processing file: {csv_path}")
            populate_from_csv(session, csv_path)
    session.close()


if __name__ == "__main__":
    main()
