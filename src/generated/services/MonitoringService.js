import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MonitoringService {
    /**
     * Monitoring
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static monitoringApiV1MonitoringDeviceIdGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/monitoring/{device_id}',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
