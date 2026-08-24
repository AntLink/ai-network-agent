import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MikrotikService {
    /**
     * Get Ip Addresses
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getIpAddressesApiV1MikrotikDeviceIdResourcesIpAddressesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/ip-addresses',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Ip Pool
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getIpPoolApiV1MikrotikDeviceIdResourcesPoolsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/pools',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Dhcp Server
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getDhcpServerApiV1MikrotikDeviceIdResourcesDhcpServersGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/dhcp-servers',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Dhcp Leases
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getDhcpLeasesApiV1MikrotikDeviceIdResourcesDhcpLeasesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/dhcp-leases',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Bridges
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getBridgesApiV1MikrotikDeviceIdResourcesBridgesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/bridges',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Bridge Ports
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getBridgePortsApiV1MikrotikDeviceIdResourcesBridgePortsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/bridge-ports',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Firewall Filter
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getFirewallFilterApiV1MikrotikDeviceIdResourcesFirewallFilterGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/firewall/filter',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Firewall Nat
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getFirewallNatApiV1MikrotikDeviceIdResourcesFirewallNatGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/firewall/nat',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Firewall Mangle
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getFirewallMangleApiV1MikrotikDeviceIdResourcesFirewallMangleGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/firewall/mangle',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Firewall Address List
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getFirewallAddressListApiV1MikrotikDeviceIdResourcesFirewallAddressListsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/firewall/address-lists',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Ospf
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getOspfApiV1MikrotikDeviceIdResourcesOspfGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/ospf',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Bgp
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getBgpApiV1MikrotikDeviceIdResourcesBgpGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/bgp',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Static Routes
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getStaticRoutesApiV1MikrotikDeviceIdResourcesStaticRoutesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/static-routes',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Ppp Secrets
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getPppSecretsApiV1MikrotikDeviceIdResourcesPppSecretsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/ppp-secrets',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Ppp Profiles
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getPppProfilesApiV1MikrotikDeviceIdResourcesPppProfilesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/ppp-profiles',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Wireless
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getWirelessApiV1MikrotikDeviceIdResourcesWirelessGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/wireless',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Wireless Security Profiles
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getWirelessSecurityProfilesApiV1MikrotikDeviceIdResourcesWirelessSecurityProfilesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/wireless-security-profiles',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Snmp
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getSnmpApiV1MikrotikDeviceIdResourcesSnmpGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/snmp',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get System Users
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getSystemUsersApiV1MikrotikDeviceIdResourcesUsersGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/users',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get System Logging
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getSystemLoggingApiV1MikrotikDeviceIdResourcesLoggingGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/logging',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Ip Address
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addIpAddressApiV1MikrotikDeviceIdIpAddressPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/ip-address',
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
     * Remove Ip Address
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeIpAddressApiV1MikrotikDeviceIdIpAddressDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/ip-address',
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
     * Add Vlan
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addVlanApiV1MikrotikDeviceIdVlanPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/vlan',
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
     * Remove Vlan
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeVlanApiV1MikrotikDeviceIdVlanDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/vlan',
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
     * Add Bridge
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addBridgeApiV1MikrotikDeviceIdBridgePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/bridge',
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
     * Add Bridge Port
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addBridgePortApiV1MikrotikDeviceIdBridgePortPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/bridge/port',
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
     * Remove Bridge Port
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeBridgePortApiV1MikrotikDeviceIdBridgePortDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/bridge/port',
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
     * Add Static Route
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addStaticRouteApiV1MikrotikDeviceIdStaticRoutePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/static-route',
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
    static removeStaticRouteApiV1MikrotikDeviceIdStaticRouteDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/static-route',
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
     * Add Firewall Filter
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addFirewallFilterApiV1MikrotikDeviceIdFirewallFilterPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/firewall/filter',
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
     * Remove Firewall Filter
     * @param deviceId
     * @param ruleNumber
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeFirewallFilterApiV1MikrotikDeviceIdFirewallFilterRuleNumberDelete(deviceId, ruleNumber) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/firewall/filter/{rule_number}',
            path: {
                'device_id': deviceId,
                'rule_number': ruleNumber,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Firewall Nat
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addFirewallNatApiV1MikrotikDeviceIdFirewallNatPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/firewall/nat',
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
     * Remove Firewall Nat
     * @param deviceId
     * @param ruleNumber
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeFirewallNatApiV1MikrotikDeviceIdFirewallNatRuleNumberDelete(deviceId, ruleNumber) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/firewall/nat/{rule_number}',
            path: {
                'device_id': deviceId,
                'rule_number': ruleNumber,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Address List Entry
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addAddressListEntryApiV1MikrotikDeviceIdFirewallAddressListPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/firewall/address-list',
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
     * Remove Address List Entry
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeAddressListEntryApiV1MikrotikDeviceIdFirewallAddressListDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/firewall/address-list',
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
     * Add Ip Pool
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addIpPoolApiV1MikrotikDeviceIdIpPoolPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/ip-pool',
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
     * Remove Ip Pool
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeIpPoolApiV1MikrotikDeviceIdIpPoolDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/ip-pool',
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
     * Add Dhcp Server
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addDhcpServerApiV1MikrotikDeviceIdDhcpServerPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/dhcp-server',
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
     * Set Interface
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setInterfaceApiV1MikrotikDeviceIdInterfaceSetPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/interface/set',
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
     * Enable Interface
     * @param deviceId
     * @param name
     * @returns any Successful Response
     * @throws ApiError
     */
    static enableInterfaceApiV1MikrotikDeviceIdInterfaceNameEnablePost(deviceId, name) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/interface/{name}/enable',
            path: {
                'device_id': deviceId,
                'name': name,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Disable Interface
     * @param deviceId
     * @param name
     * @returns any Successful Response
     * @throws ApiError
     */
    static disableInterfaceApiV1MikrotikDeviceIdInterfaceNameDisablePost(deviceId, name) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/interface/{name}/disable',
            path: {
                'device_id': deviceId,
                'name': name,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set Identity
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setIdentityApiV1MikrotikDeviceIdSystemIdentityPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/system/identity',
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
     * Add System User
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addSystemUserApiV1MikrotikDeviceIdSystemUsersPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/system/users',
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
     * Remove System User
     * @param deviceId
     * @param name
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeSystemUserApiV1MikrotikDeviceIdSystemUsersNameDelete(deviceId, name) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/system/users/{name}',
            path: {
                'device_id': deviceId,
                'name': name,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set Ntp Client
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setNtpClientApiV1MikrotikDeviceIdSystemNtpPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/system/ntp',
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
    static setDnsApiV1MikrotikDeviceIdSystemDnsPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/system/dns',
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
     * Add Wireless Security Profile
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addWirelessSecurityProfileApiV1MikrotikDeviceIdWirelessSecurityProfilePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/wireless/security-profile',
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
     * Get Hotspot Servers
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getHotspotServersApiV1MikrotikDeviceIdResourcesHotspotServersGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/hotspot/servers',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Hotspot Profiles
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getHotspotProfilesApiV1MikrotikDeviceIdResourcesHotspotProfilesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/hotspot/profiles',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Hotspot Users
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getHotspotUsersApiV1MikrotikDeviceIdResourcesHotspotUsersGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/hotspot/users',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Hotspot User Profiles
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getHotspotUserProfilesApiV1MikrotikDeviceIdResourcesHotspotUserProfilesGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/hotspot/user-profiles',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Hotspot Active
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getHotspotActiveApiV1MikrotikDeviceIdResourcesHotspotActiveGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/hotspot/active',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Hotspot Hosts
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getHotspotHostsApiV1MikrotikDeviceIdResourcesHotspotHostsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/hotspot/hosts',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Hotspot Ip Bindings
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getHotspotIpBindingsApiV1MikrotikDeviceIdResourcesHotspotIpBindingsGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/hotspot/ip-bindings',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Hotspot Walled Garden
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getHotspotWalledGardenApiV1MikrotikDeviceIdResourcesHotspotWalledGardenGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/hotspot/walled-garden',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Hotspot Server
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addHotspotServerApiV1MikrotikDeviceIdHotspotServerPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/hotspot/server',
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
     * Remove Hotspot Server
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeHotspotServerApiV1MikrotikDeviceIdHotspotServerDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/hotspot/server',
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
     * Enable Hotspot Server
     * @param deviceId
     * @param name
     * @returns any Successful Response
     * @throws ApiError
     */
    static enableHotspotServerApiV1MikrotikDeviceIdHotspotServerNameEnablePost(deviceId, name) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/hotspot/server/{name}/enable',
            path: {
                'device_id': deviceId,
                'name': name,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Disable Hotspot Server
     * @param deviceId
     * @param name
     * @returns any Successful Response
     * @throws ApiError
     */
    static disableHotspotServerApiV1MikrotikDeviceIdHotspotServerNameDisablePost(deviceId, name) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/hotspot/server/{name}/disable',
            path: {
                'device_id': deviceId,
                'name': name,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Hotspot User
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addHotspotUserApiV1MikrotikDeviceIdHotspotUserPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/hotspot/user',
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
     * Remove Hotspot User
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeHotspotUserApiV1MikrotikDeviceIdHotspotUserDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/hotspot/user',
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
     * Set Hotspot User
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setHotspotUserApiV1MikrotikDeviceIdHotspotUserPatch(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/mikrotik/{device_id}/hotspot/user',
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
     * Reset Hotspot User Counters
     * @param deviceId
     * @param name
     * @returns any Successful Response
     * @throws ApiError
     */
    static resetHotspotUserCountersApiV1MikrotikDeviceIdHotspotUserNameResetCountersPost(deviceId, name) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/hotspot/user/{name}/reset-counters',
            path: {
                'device_id': deviceId,
                'name': name,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Reset All Hotspot Counters
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static resetAllHotspotCountersApiV1MikrotikDeviceIdHotspotResetCountersAllPost(deviceId) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/hotspot/reset-counters-all',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Kick Hotspot User
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static kickHotspotUserApiV1MikrotikDeviceIdHotspotKickPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/hotspot/kick',
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
     * Add Hotspot User Profile
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addHotspotUserProfileApiV1MikrotikDeviceIdHotspotUserProfilePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/hotspot/user-profile',
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
     * Remove Hotspot User Profile
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeHotspotUserProfileApiV1MikrotikDeviceIdHotspotUserProfileDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/hotspot/user-profile',
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
     * Add Hotspot Ip Binding
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addHotspotIpBindingApiV1MikrotikDeviceIdHotspotIpBindingPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/hotspot/ip-binding',
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
     * Remove Hotspot Ip Binding
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeHotspotIpBindingApiV1MikrotikDeviceIdHotspotIpBindingDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/hotspot/ip-binding',
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
     * Get Ppp Active
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getPppActiveApiV1MikrotikDeviceIdResourcesPppActiveGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/ppp-active',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Ppp Secret
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addPppSecretApiV1MikrotikDeviceIdPppSecretPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/ppp/secret',
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
     * Remove Ppp Secret
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removePppSecretApiV1MikrotikDeviceIdPppSecretDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/ppp/secret',
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
     * Set Ppp Secret
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setPppSecretApiV1MikrotikDeviceIdPppSecretPatch(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/mikrotik/{device_id}/ppp/secret',
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
     * Kick Ppp Session
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static kickPppSessionApiV1MikrotikDeviceIdPppKickPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/ppp/kick',
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
     * Get Tunnel Server Status
     * @param deviceId
     * @param tunnelType
     * @returns any Successful Response
     * @throws ApiError
     */
    static getTunnelServerStatusApiV1MikrotikDeviceIdResourcesTunnelTunnelTypeServerGet(deviceId, tunnelType) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/tunnel/{tunnel_type}/server',
            path: {
                'device_id': deviceId,
                'tunnel_type': tunnelType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set Tunnel Server
     * @param deviceId
     * @param tunnelType
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static setTunnelServerApiV1MikrotikDeviceIdTunnelTunnelTypeServerPatch(deviceId, tunnelType, requestBody) {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/mikrotik/{device_id}/tunnel/{tunnel_type}/server',
            path: {
                'device_id': deviceId,
                'tunnel_type': tunnelType,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Pppoe Servers
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getPppoeServersApiV1MikrotikDeviceIdResourcesPppoeServersGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/pppoe-servers',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Pppoe Server Instance
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addPppoeServerInstanceApiV1MikrotikDeviceIdPppoeServerInstancePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/pppoe/server-instance',
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
     * Remove Pppoe Server Instance
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removePppoeServerInstanceApiV1MikrotikDeviceIdPppoeServerInstanceDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/pppoe/server-instance',
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
     * Get Tunnel Clients
     * @param deviceId
     * @param tunnelType
     * @returns any Successful Response
     * @throws ApiError
     */
    static getTunnelClientsApiV1MikrotikDeviceIdResourcesTunnelTunnelTypeClientsGet(deviceId, tunnelType) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/resources/tunnel/{tunnel_type}/clients',
            path: {
                'device_id': deviceId,
                'tunnel_type': tunnelType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Tunnel Client
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addTunnelClientApiV1MikrotikDeviceIdTunnelClientPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/tunnel/client',
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
     * Remove Tunnel Client
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeTunnelClientApiV1MikrotikDeviceIdTunnelClientDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/tunnel/client',
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
     * Manage Tunnel Client
     * @param deviceId
     * @param tunnelType
     * @param name
     * @param action
     * @returns any Successful Response
     * @throws ApiError
     */
    static manageTunnelClientApiV1MikrotikDeviceIdTunnelTunnelTypeClientNameActionPost(deviceId, tunnelType, name, action) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/tunnel/{tunnel_type}/client/{name}/{action}',
            path: {
                'device_id': deviceId,
                'tunnel_type': tunnelType,
                'name': name,
                'action': action,
            },
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
    static runCommandsApiV1MikrotikDeviceIdCommandsRunPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/commands/run',
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
     * Get Monitoring
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static getMonitoringApiV1MikrotikDeviceIdMonitoringPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/monitoring',
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
     * Get Health
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    static getHealthApiV1MikrotikDeviceIdHealthGet(deviceId) {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mikrotik/{device_id}/health',
            path: {
                'device_id': deviceId,
            },
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
    static pingToolApiV1MikrotikDeviceIdToolsPingPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/tools/ping',
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
    static tracerouteToolApiV1MikrotikDeviceIdToolsTraceroutePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/tools/traceroute',
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
     * Config Transaction
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static configTransactionApiV1MikrotikDeviceIdConfigTransactionPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/config/transaction',
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
     * Add Ospf Instance
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addOspfInstanceApiV1MikrotikDeviceIdOspfInstancePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/ospf/instance',
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
     * Remove Ospf Instance
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeOspfInstanceApiV1MikrotikDeviceIdOspfInstanceDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/ospf/instance',
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
     * Add Ospf Area
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addOspfAreaApiV1MikrotikDeviceIdOspfAreaPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/ospf/area',
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
     * Add Ospf Interface Template
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addOspfInterfaceTemplateApiV1MikrotikDeviceIdOspfInterfaceTemplatePost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/ospf/interface-template',
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
     * Add Ospf Network
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static addOspfNetworkApiV1MikrotikDeviceIdOspfNetworkPost(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/ospf/network',
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
     * Remove Ospf Network
     * @param deviceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    static removeOspfNetworkApiV1MikrotikDeviceIdOspfNetworkDelete(deviceId, requestBody) {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/mikrotik/{device_id}/ospf/network',
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
    static saveConfigApiV1MikrotikDeviceIdConfigSavePost(deviceId) {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/mikrotik/{device_id}/config/save',
            path: {
                'device_id': deviceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
