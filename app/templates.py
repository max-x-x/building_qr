from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    email: str
    password: str

class LocationRequest(BaseModel):
    latitude: float
    longitude: float

class LocationRequestWithToken(BaseModel):
    token: str
    latitude: float
    longitude: float
    object_id: int


class PhotoRequest(BaseModel):
    imageBase64: str = Field(..., description="Base64 encoded image string")

class LocationResponse(BaseModel):
    status: str
    location_granted: bool
    message: str
