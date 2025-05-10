from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db import Base


class Airline(Base):
    __tablename__ = 'airline'

    id = Column(Integer, primary_key=True)
    airline_name = Column(String)
    airline_iata = Column(String)
    airline_icao = Column(String)

    flights = relationship("Flight", back_populates="airline")
