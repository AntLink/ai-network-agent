import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ConfigService {
    /**
     * Create Plan
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static createPlanApiV1ConfigPlanPost(requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/config/plan',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Apply Plan
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static applyPlanApiV1ConfigApplyPost(requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/config/apply',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Rollback
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static rollbackApiV1ConfigRollbackPost(requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/config/rollback',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
