import math

from fastapi import APIRouter

from app.api import APIClient
from ..templates import LocationRequestWithToken, LocationResponse

router = APIRouter()


@router.post("/", response_model=LocationResponse)
async def send_location(location_data: LocationRequestWithToken):
    client = APIClient()
    polygon = client.get_poligon(location_data.object_id, location_data.token)

    if not polygon or len(polygon) < 3:
        return LocationResponse(
            status="error", 
            location_granted=False, 
            message="Полигон не найден"
        )

    latitudes = [p[0] for p in polygon]
    longitudes = [p[1] for p in polygon]
    center_lat = sum(latitudes) / len(latitudes)
    center_lon = sum(longitudes) / len(longitudes)

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (math.sin(dphi / 2) ** 2 + 
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    distance_km = haversine(
        center_lat, 
        center_lon, 
        location_data.latitude, 
        location_data.longitude
    )
    inside = distance_km <= 5.0

    if inside:
        return LocationResponse(
            status="success", 
            location_granted=True, 
            message="Геопозиция подтверждена"
        )
    else:
        return LocationResponse(
            status="success", 
            location_granted=False, 
            message="Геопозиция вне разрешенной зоны"
        )