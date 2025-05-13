from geopy.geocoders import Nominatim

def get_coordinates(place_name: str):
    try:
        geolocator = Nominatim(user_agent="kundali_app")
        location = geolocator.geocode(place_name)
    except Exception as e:
        print(f"Error while getting coordinates: {e}")
        return {}
    if location:
        return {"latitude": location.latitude, "longitude": location.longitude}
    return {}

if __name__ == "__main__":
    print(get_coordinates("Ahmedabad, India"))