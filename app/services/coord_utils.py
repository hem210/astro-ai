from geopy.geocoders import Nominatim

def get_coordinates(place_name: str):
    geolocator = Nominatim(user_agent="kundali_app")
    location = geolocator.geocode(place_name)
    if location:
        return {"latitude": location.latitude, "longitude": location.longitude}
    return None

if __name__ == "__main__":
    print(get_coordinates("Ahmedabad, India"))