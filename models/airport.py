from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from db import Base


class Airport(Base):
    __tablename__ = 'airport'

    id = Column(Integer, primary_key=True)
    airport_name = Column(String)
    airport_iata = Column(String)
    airport_icao = Column(String)
    timezone = Column(String)
    latitude = Column(Float)    # new columns
    longitude = Column(Float)

    departures = relationship(
        "Flight", back_populates="departure_airport", foreign_keys='Flight.dep_airport_id')
    arrivals = relationship(
        "Flight", back_populates="arrival_airport", foreign_keys='Flight.arr_airport_id')
