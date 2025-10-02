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

    def point_in_polygon(x, y, polygon):
        inside = False
        n = len(polygon)
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    
    inside = point_in_polygon(
        location_data.longitude, 
        location_data.latitude, 
        polygon
    )
    

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