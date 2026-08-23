from fastapi import APIRouter, Request, HTTPException
from app.drivers.factory import get_driver
from app.repositories.inventory import inventory_repository
from app.drivers.cisco.parser import IOSParser

router = APIRouter()


@router.get("/{device_id}")
@router.post("/{device_id}")
async def monitoring(device_id: str, request: Request = None):
    """Get monitoring data (CPU, memory, disk, etc) for a device.
    
    Returns structured JSON with:
    - device_info: Device identification
    - cpu: CPU utilization statistics
    - memory: Memory usage statistics  
    - interfaces: Interface status
    - health: Device health check
    """
    try:
        device = inventory_repository.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
        
        driver = get_driver(device)
        
        # Build monitoring data structure
        monitoring_data = {
            "device_id": device_id,
            "hostname": device.get("hostname", ""),
            "vendor": device.get("vendor", ""),
            "management_address": device.get("management_address", ""),
        }
        
        # Get CPU and Memory with parsing
        if hasattr(driver, 'get_cpu_memory'):
            try:
                cpu_mem = await driver.get_cpu_memory()
                # Use parsed data if available, otherwise use raw
                if cpu_mem.get("data"):
                    monitoring_data["cpu_memory"] = cpu_mem["data"]
                else:
                    monitoring_data["cpu_memory_raw"] = cpu_mem.get("raw", "")
            except Exception as e:
                monitoring_data["cpu_memory_error"] = str(e)
        
        # Get interfaces
        if hasattr(driver, 'get_interfaces'):
            try:
                interfaces = await driver.get_interfaces()
                if interfaces.get("data"):
                    monitoring_data["interfaces"] = interfaces["data"]
                else:
                    monitoring_data["interfaces_raw"] = interfaces.get("raw", "")
            except Exception as e:
                monitoring_data["interfaces_error"] = str(e)
        
        # Get health check
        if hasattr(driver, 'health'):
            try:
                health = await driver.health()
                monitoring_data["health"] = health
            except Exception as e:
                monitoring_data["health_error"] = str(e)
        
        # Get routes
        if hasattr(driver, 'get_routes'):
            try:
                routes = await driver.get_routes()
                if routes.get("data"):
                    monitoring_data["routes"] = routes["data"]
                else:
                    monitoring_data["routes_raw"] = routes.get("raw", "")
            except Exception as e:
                monitoring_data["routes_error"] = str(e)
        
        # Get facts (includes version, uptime, etc.)
        if hasattr(driver, 'get_facts'):
            try:
                facts = await driver.get_facts()
                if facts.get("data"):
                    monitoring_data["facts"] = facts["data"]
                else:
                    monitoring_data["facts_raw"] = facts.get("raw", "")
            except Exception as e:
                monitoring_data["facts_error"] = str(e)
        
        return monitoring_data
        
    except HTTPException:
        raise
    except Exception as e:
        return {"device_id": device_id, "status": "error", "error": str(e)}
