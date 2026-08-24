import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TopologyService {
    /**
     * Topology
     * @returns any Successful Response
     * @throws ApiError
     */
    static topologyApiV1TopologyGet() {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/topology',
        });
    }
}
