import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AuditService {
    /**
     * Audit Events
     * @returns any Successful Response
     * @throws ApiError
     */
    static auditEventsApiV1AuditGet() {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/audit',
        });
    }
}
