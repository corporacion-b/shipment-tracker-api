from src.db.connection import database


class LocationRepository:
    @staticmethod
    def get_or_create_location(country_code: str, city: str, latitude: float, longitude: float) -> int:
        """Busca una ubicación por ciudad y país, si no existe la crea. Devuelve el ID."""
        lat = latitude if latitude is not None else 0.0
        lon = longitude if longitude is not None else 0.0
        with database.connect() as connection:
            cursor = connection.cursor()
            
            select_query = "SELECT id_location, latitude, longitude FROM locations WHERE country_code = %s AND city = %s"
            cursor.execute(select_query, (country_code, city))
            result = cursor.fetchone()
            
            if result:
                if (
                    result["latitude"] == 0.0 and result["longitude"] == 0.0
                ) and (lat != 0.0 or lon != 0.0):
                    update_query = """
                        UPDATE locations 
                        SET latitude = %s, longitude = %s 
                        WHERE id_location = %s
                    """
                    cursor.execute(update_query, (lat, lon, result["id_location"]))
                return result["id_location"]

            insert_query = """
                INSERT INTO locations (country_code, city, latitude, longitude) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (country_code, city, lat, lon))
            return cursor.lastrowid