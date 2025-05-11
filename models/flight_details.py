from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db import Base


class FlightDetails(Base):
    __tablename__ = "flight_details"

    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String)
    call_sign = Column(String)

    # Relationships
    flights = relationship("Flight", back_populates="flight_details")
