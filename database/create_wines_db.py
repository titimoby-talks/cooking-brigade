import json
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from database.Wine import Wine, Base

# Define database file path
DB_FILE = 'sqlite:///database/wines.db'

# Create the SQLAlchemy engine
engine = create_engine(DB_FILE, echo=True)

# Define the Wine model

def main():
    # Drop tables if they exist to apply changes
    Base.metadata.drop_all(engine)
    # Create tables
    Base.metadata.create_all(engine)
    print("Database tables created.")

    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Load data from JSON
        with open('./database/wines_seed.json', 'r', encoding='utf-8') as f:
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
                year=item.get("year")
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
    main()