from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "CSMS Monitor"
    APP_VERSION: str = "1.0.0"
    
    # CSMS Device
    CSMS_HOST: str = "192.168.162.20"
    CSMS_SSH_PORT: int = 22
    CSMS_SSH_USER: str = "root"
    CSMS_SSH_PASS: str = "815m1ll4h"
    CSMS_SCPI_PORT: int = 5025
    CSMS_GPS_PORT: int = 2947
    
    # CSMS Bridge API
    CSMS_BRIDGE_URL: str = "http://192.168.162.20:8080"
    
    # App
    API_PREFIX: str = "/api/v1"
    WS_PATH: str = "/ws"
    
    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
