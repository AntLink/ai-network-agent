import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CiscoService {
    /**
     * Get Version
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getVersionApiV1CiscoDeviceIdResourcesVersionGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/cisco/{device_id}/resources/version',
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
    static getInterfacesApiV1CiscoDeviceIdResourcesInterfacesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/cisco/{device_id}/resources/interfaces',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Interfaces Detail
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getInterfacesDetailApiV1CiscoDeviceIdResourcesInterfacesDetailGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/cisco/{device_id}/resources/interfaces-detail',
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
    static getRoutesApiV1CiscoDeviceIdResourcesRoutesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/cisco/{device_id}/resources/routes',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Arp
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getArpApiV1CiscoDeviceIdResourcesArpGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/cisco/{device_id}/resources/arp',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Cpu Memory
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getCpuMemoryApiV1CiscoDeviceIdResourcesCpuMemoryGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/cisco/{device_id}/resources/cpu-memory',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Acls
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getAclsApiV1CiscoDeviceIdResourcesAclsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/cisco/{device_id}/resources/acls',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Cdp Neighbors
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getCdpNeighborsApiV1CiscoDeviceIdResourcesCdpNeighborsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/cisco/{device_id}/resources/cdp-neighbors',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Nat Translations
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getNatTranslationsApiV1CiscoDeviceIdResourcesNatTranslationsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/cisco/{device_id}/resources/nat-translations',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Logs
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getLogsApiV1CiscoDeviceIdResourcesLogsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/cisco/{device_id}/resources/logs',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set Hostname
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setHostnameApiV1CiscoDeviceIdSystemHostnamePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/system/hostname',
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
     * Set Dns
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setDnsApiV1CiscoDeviceIdSystemDnsPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/system/dns',
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
     * Add Ntp Server
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addNtpServerApiV1CiscoDeviceIdSystemNtpPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/system/ntp',
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
     * Remove Ntp Server
     * @param deviceId
     * @param server
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeNtpServerApiV1CiscoDeviceIdSystemNtpServerDelete(deviceId, server) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/cisco/{device_id}/system/ntp/{server}',
            path: {
                'device_id': deviceId,
                'server': server,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set Banner
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setBannerApiV1CiscoDeviceIdSystemBannerPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/system/banner',
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
     * Create Local User
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static createLocalUserApiV1CiscoDeviceIdUsersPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/users',
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
     * Delete Local User
     * @param deviceId
     * @param username
     * @returns any Successful Response
     * @throws ApiError
     */
    static deleteLocalUserApiV1CiscoDeviceIdUsersUsernameDelete(deviceId, username) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/cisco/{device_id}/users/{username}',
            path: {
                'device_id': deviceId,
                'username': username,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Interface Description
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static interfaceDescriptionApiV1CiscoDeviceIdInterfaceDescriptionPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/interface/description',
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
     * Interface Address
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static interfaceAddressApiV1CiscoDeviceIdInterfaceAddressPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/interface/address',
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
     * Interface Remove Address
     * @param deviceId
     * @param _interface
     * @returns any Successful Response
     * @throws ApiError
     */
    static interfaceRemoveAddressApiV1CiscoDeviceIdInterfaceInterfaceAddressDelete(deviceId, _interface) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/cisco/{device_id}/interface/{interface}/address',
            path: {
                'device_id': deviceId,
                'interface': _interface,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Interface Mtu
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static interfaceMtuApiV1CiscoDeviceIdInterfaceMtuPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/interface/mtu',
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
     * Interface State
     * @param deviceId
     * @param name
     * @param action
     * @returns any Successful Response
     * @throws ApiError
     */
    static interfaceStateApiV1CiscoDeviceIdInterfaceNameActionPost(deviceId, name, action) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/interface/{name}/{action}',
            path: {
                'device_id': deviceId,
                'name': name,
                'action': action,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Static Route
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addStaticRouteApiV1CiscoDeviceIdStaticRoutePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/static-route',
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
     * Remove Static Route
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeStaticRouteApiV1CiscoDeviceIdStaticRouteDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/cisco/{device_id}/static-route',
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
     * Create Acl
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static createAclApiV1CiscoDeviceIdAclPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/acl',
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
     * Delete Acl
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static deleteAclApiV1CiscoDeviceIdAclDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/cisco/{device_id}/acl',
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
     * Apply Acl
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static applyAclApiV1CiscoDeviceIdAclApplyPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/acl/apply',
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
     * Unapply Acl
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static unapplyAclApiV1CiscoDeviceIdAclUnapplyPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/acl/unapply',
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
     * Create Vlan
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static createVlanApiV1CiscoDeviceIdL2VlanPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/l2/vlan',
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
     * Delete Vlan
     * @param deviceId
     * @param vlanId
     * @returns any Successful Response
     * @throws ApiError
     */
    static deleteVlanApiV1CiscoDeviceIdL2VlanVlanIdDelete(deviceId, vlanId) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/cisco/{device_id}/l2/vlan/{vlan_id}',
            path: {
                'device_id': deviceId,
                'vlan_id': vlanId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set Access Port
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setAccessPortApiV1CiscoDeviceIdL2AccessPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/l2/access',
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
     * Set Trunk Port
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setTrunkPortApiV1CiscoDeviceIdL2TrunkPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/l2/trunk',
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
     * Create Subinterface
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static createSubinterfaceApiV1CiscoDeviceIdL2SubinterfacePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/l2/subinterface',
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
     * Set Svi
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setSviApiV1CiscoDeviceIdL2SviPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/l2/svi',
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
     * Run Commands
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static runCommandsApiV1CiscoDeviceIdCommandsRunPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/commands/run',
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
     * Ping Tool
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static pingToolApiV1CiscoDeviceIdToolsPingPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/tools/ping',
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
     * Traceroute Tool
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static tracerouteToolApiV1CiscoDeviceIdToolsTraceroutePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/tools/traceroute',
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
     * Save Config
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static saveConfigApiV1CiscoDeviceIdConfigSavePost(deviceId) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/config/save',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Config Transaction
     * Transaksi konfigurasi: backup -> apply -> verify -> commit | rollback.
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static configTransactionApiV1CiscoDeviceIdConfigTransactionPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/config/transaction',
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
     * Backup Config
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static backupConfigApiV1CiscoDeviceIdConfigBackupPost(deviceId) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/config/backup',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Netmiko Config Push
     * Push configuration using Netmiko with proper enable/config/save flow.
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static netmikoConfigPushApiV1CiscoDeviceIdConfigPushPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/config/push',
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
     * Netmiko Exec
     * Run exec commands via Netmiko (proper prompt handling).
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static netmikoExecApiV1CiscoDeviceIdExecPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/cisco/{device_id}/exec',
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
}
