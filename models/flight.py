from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db import Base


class Flight(Base):
    __tablename__ = 'flight'

    id = Column(Integer, primary_key=True)
    status = Column(String)
    flight_details_id = Column(Integer, ForeignKey(
        'flight_details.id'), nullable=False)
    arline_id = Column(Integer, ForeignKey('airline.id'))
    airplane_id = Column(Integer, ForeignKey('airplane.id'))
    dep_airport_id = Column(Integer, ForeignKey('airport.id'))
    arr_airport_id = Column(Integer, ForeignKey('airport.id'))
    dep_date_time_UTC = Column(DateTime)
    dep_rev_date_time_UTC = Column(DateTime)
    arr_date_time_UTC = Column(DateTime)
    arr_rev_date_time_UTC = Column(DateTime)

    flight_details = relationship("FlightDetails", back_populates="flights")
    airline = relationship("Airline", back_populates="flights")
    airplane = relationship("Airplane", back_populates="flights")
    departure_airport = relationship(
        "Airport", back_populates="departures", foreign_keys=[dep_airport_id])
    arrival_airport = relationship(
        "Airport", back_populates="arrivals", foreign_keys=[arr_airport_id])
