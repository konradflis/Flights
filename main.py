import os  # Added to handle file operations
from db import engine
from models import Airline, Airport, Airplane, Flight, FlightDetails
from db import Base


def delete_old_db():
    db_path = "flights.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted old database at {db_path}")
    else:
        print(f"No database found at {db_path} to delete.")


def init_db():
    delete_old_db()  # Call the function to delete the old database
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
