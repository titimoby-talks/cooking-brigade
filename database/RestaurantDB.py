import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.Wine import Wine, Base

class RestaurantDB:
    def __init__(self, db_url='sqlite:///database/wines.db'):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Creates all tables defined in the metadata."""
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        """Drops all tables defined in the metadata."""
        Base.metadata.drop_all(self.engine)

    def get_session(self):
        return self.Session()

    def get_all_wines(self):
        """Returns all wines from the database."""
        session = self.get_session()
        try:
            return session.query(Wine).all()
        finally:
            session.close()

    def get_wine_by_name(self, name):
        """Returns a single wine by its unique name."""
        session = self.get_session()
        try:
            return session.query(Wine).filter(Wine.name == name).first()
        finally:
            session.close()

    def query_wines(self, **kwargs):
        """
        Generic query method. 
        Example: db.query_wines(wine_type="Rouge", region="Bordeaux")
        """
        session = self.get_session()
        try:
            query = session.query(Wine)
            for key, value in kwargs.items():
                if hasattr(Wine, key):
                    query = query.filter(getattr(Wine, key) == value)
            return query.all()
        finally:
            session.close()

    def seed_wines(self, seed_file):
        """Seeds the database with wines from the seed file."""
        session = self.get_session()

        try:
            with open(seed_file, 'r', encoding='utf-8') as f:
                wine_data = json.load(f)

            print(f"Loaded {len(wine_data)} wines from JSON.")
            # Populate the database
            for item in wine_data:
                wine = Wine(
                    name=item.get("name"),
                    wine_type=item.get("wine_type"),
                    region=item.get("region"),
                    grape_variety=item.get("grape_variety"),
                    characteristics=item.get("characteristics"),
                    body=item.get("body"),
                    acidity=item.get("acidity"),
                    pairing_notes=item.get("pairing_notes"),
                    serving_temp_celsius=item.get("serving_temp_celsius"),
                    price_per_bottle=item.get("price_per_bottle"),
                    stock_quantity=item.get("stock_quantity"),
                    year=item.get("year"),
                )
                session.add(wine)

            # Commit changes
            session.commit()
            print("Data successfully inserted into the database.")

            # Print total records
            total_wines = session.query(Wine).count()
            print(f"Total records in wine table: {total_wines}")

        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
        finally:
            session.close()


if __name__ == "__main__":
    # Quick test
    db = RestaurantDB()
    db.drop_tables()
    db.create_tables()
    db.seed_wines(seed_file="./database/wines_seed.json")

    all_wines = db.get_all_wines()
    print(f"Total wines in DB: {len(all_wines)}")
    if all_wines:
        print(f"First wine: {all_wines[0].name}")
