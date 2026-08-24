/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ConfigApplyRequest } from '../models/ConfigApplyRequest';
import type { ConfigPlanRequest } from '../models/ConfigPlanRequest';
import type { ConfigRollbackRequest } from '../models/ConfigRollbackRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ConfigService {
    /**
     * Create Plan
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createPlanApiV1ConfigPlanPost(
        requestBody: ConfigPlanRequest,
    ): CancelablePromise<any> {
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
    public static applyPlanApiV1ConfigApplyPost(
        requestBody: ConfigApplyRequest,
    ): CancelablePromise<any> {
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
    public static rollbackApiV1ConfigRollbackPost(
        requestBody: ConfigRollbackRequest,
    ): CancelablePromise<any> {
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
