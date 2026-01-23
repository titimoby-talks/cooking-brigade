from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

# Define the base class for ORM models
Base = declarative_base()

class Wine(Base):
    __tablename__ = 'wines'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True, index=True)
    wine_type = Column(String)
    region = Column(String)
    grape_variety = Column(String)
    characteristics = Column(String)
    body = Column(String)
    acidity = Column(String)
    pairing_notes = Column(String)
    serving_temp_celsius = Column(Integer)
    price_per_bottle = Column(Float)
    stock_quantity = Column(Integer)
    year = Column(Integer)

    def string_representation(self):
        return " ".join(str(getattr(self, c.name)) for c in self.__table__.columns if getattr(self, c.name) is not None)
