import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DevicesService {
    /**
     * List Devices
     * @returns any Successful Response
     * @throws ApiError
     */
    static listDevicesApiV1DevicesGet() {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices',
        });
    }
    /**
     * Get Device Health
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getDeviceHealthApiV1DevicesDeviceIdHealthGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/health',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Console Exec
     * Run one command over telnet console (recovery path when SSH is down).
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static consoleExecApiV1DevicesDeviceIdConsoleExecPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/devices/{device_id}/console/exec',
            path: {
                'device_id': deviceId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Identify Device
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static identifyDeviceApiV1DevicesDeviceIdIdentifyGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/identify',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Facts
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getFactsApiV1DevicesDeviceIdFactsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/facts',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Interfaces
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getInterfacesApiV1DevicesDeviceIdInterfacesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/interfaces',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Routes
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getRoutesApiV1DevicesDeviceIdRoutesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/routes',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Config
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getConfigApiV1DevicesDeviceIdConfigGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/config',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Vlans
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getVlansApiV1DevicesDeviceIdVlansGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/vlans',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Services
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getServicesApiV1DevicesDeviceIdServicesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/services',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Disk
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getDiskApiV1DevicesDeviceIdDiskGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/disk',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Memory
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getMemoryApiV1DevicesDeviceIdMemoryGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/memory',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Ntp
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getNtpApiV1DevicesDeviceIdNtpGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/devices/{device_id}/ntp',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
