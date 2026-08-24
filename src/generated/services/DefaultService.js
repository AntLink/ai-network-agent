import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
    /**
     * Health
     * @returns any Successful Response
     * @throws ApiError
     */
    static healthHealthGet() {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/health',
        });
    }
}
