from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db import Base


class Airplane(Base):
    __tablename__ = 'airplane'

    id = Column(Integer, primary_key=True)
    aircraft_model = Column(String)
    aircraft_reg = Column(String)

    flights = relationship("Flight", back_populates="airplane")
