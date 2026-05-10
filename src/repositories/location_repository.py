import json
from dataclasses import dataclass

from src.db.connection import database

@dataclass(frozen=True)
class NormalizedOriginDestination:
    country_code: str
    city: str

class LocationRepository:
    @staticmethod
    def get_or_create_location(country_code: str, city: str) -> int:
        """Busca una ubicación por ciudad y país, si no existe la crea. Devuelve el ID."""
        with database.connect() as connection:
            cursor = connection.cursor()
            
            select_query = "SELECT id_location FROM locations WHERE country_code = %s AND city = %s"
            cursor.execute(select_query, (country_code, city))
            result = cursor.fetchone()
            
            if result:
                return result['id_location']
            
            insert_query = """
                INSERT INTO locations (country_code, city, latitude, longitude) 
                VALUES (%s, %s, 0.0, 0.0)
            """
            cursor.execute(insert_query, (country_code, city))
            return cursor.lastrowid