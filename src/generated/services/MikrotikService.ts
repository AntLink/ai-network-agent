/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AddressListDelete } from '../models/AddressListDelete';
import type { AddressListEntry } from '../models/AddressListEntry';
import type { app__schemas__mikrotik__DnsSet } from '../models/app__schemas__mikrotik__DnsSet';
import type { app__schemas__mikrotik__PingRequest } from '../models/app__schemas__mikrotik__PingRequest';
import type { app__schemas__mikrotik__StaticRouteCreate } from '../models/app__schemas__mikrotik__StaticRouteCreate';
import type { app__schemas__mikrotik__StaticRouteDelete } from '../models/app__schemas__mikrotik__StaticRouteDelete';
import type { app__schemas__mikrotik__TracerouteRequest } from '../models/app__schemas__mikrotik__TracerouteRequest';
import type { app__schemas__mikrotik__VlanCreate } from '../models/app__schemas__mikrotik__VlanCreate';
import type { BridgeCreate } from '../models/BridgeCreate';
import type { BridgePortCreate } from '../models/BridgePortCreate';
import type { BridgePortDelete } from '../models/BridgePortDelete';
import type { CommandRunRequest } from '../models/CommandRunRequest';
import type { ConfigTransaction } from '../models/ConfigTransaction';
import type { DhcpServerCreate } from '../models/DhcpServerCreate';
import type { FirewallFilterCreate } from '../models/FirewallFilterCreate';
import type { FirewallNatCreate } from '../models/FirewallNatCreate';
import type { HotspotIpBindingCreate } from '../models/HotspotIpBindingCreate';
import type { HotspotIpBindingDelete } from '../models/HotspotIpBindingDelete';
import type { HotspotKickRequest } from '../models/HotspotKickRequest';
import type { HotspotNameDelete } from '../models/HotspotNameDelete';
import type { HotspotServerCreate } from '../models/HotspotServerCreate';
import type { HotspotUserCreate } from '../models/HotspotUserCreate';
import type { HotspotUserProfileCreate } from '../models/HotspotUserProfileCreate';
import type { HotspotUserUpdate } from '../models/HotspotUserUpdate';
import type { InterfaceSet } from '../models/InterfaceSet';
import type { IpAddressCreate } from '../models/IpAddressCreate';
import type { IpAddressDelete } from '../models/IpAddressDelete';
import type { IpPoolCreate } from '../models/IpPoolCreate';
import type { IpPoolDelete } from '../models/IpPoolDelete';
import type { MonitoringRequest } from '../models/MonitoringRequest';
import type { NtpClientSet } from '../models/NtpClientSet';
import type { OspfAreaCreate } from '../models/OspfAreaCreate';
import type { OspfInstanceCreate } from '../models/OspfInstanceCreate';
import type { OspfInstanceDelete } from '../models/OspfInstanceDelete';
import type { OspfInterfaceTemplateCreate } from '../models/OspfInterfaceTemplateCreate';
import type { OspfNetworkCreate } from '../models/OspfNetworkCreate';
import type { OspfNetworkDelete } from '../models/OspfNetworkDelete';
import type { PppKickRequest } from '../models/PppKickRequest';
import type { PppNameRequest } from '../models/PppNameRequest';
import type { PppoeServerCreate } from '../models/PppoeServerCreate';
import type { PppoeServerDelete } from '../models/PppoeServerDelete';
import type { PppSecretCreate } from '../models/PppSecretCreate';
import type { PppSecretUpdate } from '../models/PppSecretUpdate';
import type { SystemIdentitySet } from '../models/SystemIdentitySet';
import type { SystemUserCreate } from '../models/SystemUserCreate';
import type { TunnelClientCreate } from '../models/TunnelClientCreate';
import type { TunnelClientRequest } from '../models/TunnelClientRequest';
import type { TunnelServerSet } from '../models/TunnelServerSet';
import type { VlanDelete } from '../models/VlanDelete';
import type { WirelessSecurityProfileCreate } from '../models/WirelessSecurityProfileCreate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MikrotikService {
    /**
     * Get Ip Addresses
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getIpAddressesApiV1MikrotikDeviceIdResourcesIpAddressesGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getIpPoolApiV1MikrotikDeviceIdResourcesPoolsGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getDhcpServerApiV1MikrotikDeviceIdResourcesDhcpServersGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getDhcpLeasesApiV1MikrotikDeviceIdResourcesDhcpLeasesGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getBridgesApiV1MikrotikDeviceIdResourcesBridgesGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getBridgePortsApiV1MikrotikDeviceIdResourcesBridgePortsGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getFirewallFilterApiV1MikrotikDeviceIdResourcesFirewallFilterGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getFirewallNatApiV1MikrotikDeviceIdResourcesFirewallNatGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getFirewallMangleApiV1MikrotikDeviceIdResourcesFirewallMangleGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getFirewallAddressListApiV1MikrotikDeviceIdResourcesFirewallAddressListsGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getOspfApiV1MikrotikDeviceIdResourcesOspfGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getBgpApiV1MikrotikDeviceIdResourcesBgpGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getStaticRoutesApiV1MikrotikDeviceIdResourcesStaticRoutesGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getPppSecretsApiV1MikrotikDeviceIdResourcesPppSecretsGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getPppProfilesApiV1MikrotikDeviceIdResourcesPppProfilesGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getWirelessApiV1MikrotikDeviceIdResourcesWirelessGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getWirelessSecurityProfilesApiV1MikrotikDeviceIdResourcesWirelessSecurityProfilesGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getSnmpApiV1MikrotikDeviceIdResourcesSnmpGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getSystemUsersApiV1MikrotikDeviceIdResourcesUsersGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getSystemLoggingApiV1MikrotikDeviceIdResourcesLoggingGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static addIpAddressApiV1MikrotikDeviceIdIpAddressPost(
        deviceId: string,
        requestBody: IpAddressCreate,
    ): CancelablePromise<any> {
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
    public static removeIpAddressApiV1MikrotikDeviceIdIpAddressDelete(
        deviceId: string,
        requestBody: IpAddressDelete,
    ): CancelablePromise<any> {
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
    public static addVlanApiV1MikrotikDeviceIdVlanPost(
        deviceId: string,
        requestBody: app__schemas__mikrotik__VlanCreate,
    ): CancelablePromise<any> {
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
    public static removeVlanApiV1MikrotikDeviceIdVlanDelete(
        deviceId: string,
        requestBody: VlanDelete,
    ): CancelablePromise<any> {
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
    public static addBridgeApiV1MikrotikDeviceIdBridgePost(
        deviceId: string,
        requestBody: BridgeCreate,
    ): CancelablePromise<any> {
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
    public static addBridgePortApiV1MikrotikDeviceIdBridgePortPost(
        deviceId: string,
        requestBody: BridgePortCreate,
    ): CancelablePromise<any> {
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
    public static removeBridgePortApiV1MikrotikDeviceIdBridgePortDelete(
        deviceId: string,
        requestBody: BridgePortDelete,
    ): CancelablePromise<any> {
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
    public static addStaticRouteApiV1MikrotikDeviceIdStaticRoutePost(
        deviceId: string,
        requestBody: app__schemas__mikrotik__StaticRouteCreate,
    ): CancelablePromise<any> {
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
    public static removeStaticRouteApiV1MikrotikDeviceIdStaticRouteDelete(
        deviceId: string,
        requestBody: app__schemas__mikrotik__StaticRouteDelete,
    ): CancelablePromise<any> {
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
    public static addFirewallFilterApiV1MikrotikDeviceIdFirewallFilterPost(
        deviceId: string,
        requestBody: FirewallFilterCreate,
    ): CancelablePromise<any> {
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
    public static removeFirewallFilterApiV1MikrotikDeviceIdFirewallFilterRuleNumberDelete(
        deviceId: string,
        ruleNumber: number,
    ): CancelablePromise<any> {
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
    public static addFirewallNatApiV1MikrotikDeviceIdFirewallNatPost(
        deviceId: string,
        requestBody: FirewallNatCreate,
    ): CancelablePromise<any> {
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
    public static removeFirewallNatApiV1MikrotikDeviceIdFirewallNatRuleNumberDelete(
        deviceId: string,
        ruleNumber: number,
    ): CancelablePromise<any> {
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
    public static addAddressListEntryApiV1MikrotikDeviceIdFirewallAddressListPost(
        deviceId: string,
        requestBody: AddressListEntry,
    ): CancelablePromise<any> {
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
    public static removeAddressListEntryApiV1MikrotikDeviceIdFirewallAddressListDelete(
        deviceId: string,
        requestBody: AddressListDelete,
    ): CancelablePromise<any> {
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
    public static addIpPoolApiV1MikrotikDeviceIdIpPoolPost(
        deviceId: string,
        requestBody: IpPoolCreate,
    ): CancelablePromise<any> {
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
    public static removeIpPoolApiV1MikrotikDeviceIdIpPoolDelete(
        deviceId: string,
        requestBody: IpPoolDelete,
    ): CancelablePromise<any> {
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
    public static addDhcpServerApiV1MikrotikDeviceIdDhcpServerPost(
        deviceId: string,
        requestBody: DhcpServerCreate,
    ): CancelablePromise<any> {
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
    public static setInterfaceApiV1MikrotikDeviceIdInterfaceSetPost(
        deviceId: string,
        requestBody: InterfaceSet,
    ): CancelablePromise<any> {
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
    public static enableInterfaceApiV1MikrotikDeviceIdInterfaceNameEnablePost(
        deviceId: string,
        name: string,
    ): CancelablePromise<any> {
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
    public static disableInterfaceApiV1MikrotikDeviceIdInterfaceNameDisablePost(
        deviceId: string,
        name: string,
    ): CancelablePromise<any> {
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
    public static setIdentityApiV1MikrotikDeviceIdSystemIdentityPost(
        deviceId: string,
        requestBody: SystemIdentitySet,
    ): CancelablePromise<any> {
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
    public static addSystemUserApiV1MikrotikDeviceIdSystemUsersPost(
        deviceId: string,
        requestBody: SystemUserCreate,
    ): CancelablePromise<any> {
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
    public static removeSystemUserApiV1MikrotikDeviceIdSystemUsersNameDelete(
        deviceId: string,
        name: string,
    ): CancelablePromise<any> {
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
    public static setNtpClientApiV1MikrotikDeviceIdSystemNtpPost(
        deviceId: string,
        requestBody: NtpClientSet,
    ): CancelablePromise<any> {
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
    public static setDnsApiV1MikrotikDeviceIdSystemDnsPost(
        deviceId: string,
        requestBody: app__schemas__mikrotik__DnsSet,
    ): CancelablePromise<any> {
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
    public static addWirelessSecurityProfileApiV1MikrotikDeviceIdWirelessSecurityProfilePost(
        deviceId: string,
        requestBody: WirelessSecurityProfileCreate,
    ): CancelablePromise<any> {
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
    public static getHotspotServersApiV1MikrotikDeviceIdResourcesHotspotServersGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getHotspotProfilesApiV1MikrotikDeviceIdResourcesHotspotProfilesGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getHotspotUsersApiV1MikrotikDeviceIdResourcesHotspotUsersGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getHotspotUserProfilesApiV1MikrotikDeviceIdResourcesHotspotUserProfilesGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getHotspotActiveApiV1MikrotikDeviceIdResourcesHotspotActiveGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getHotspotHostsApiV1MikrotikDeviceIdResourcesHotspotHostsGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getHotspotIpBindingsApiV1MikrotikDeviceIdResourcesHotspotIpBindingsGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getHotspotWalledGardenApiV1MikrotikDeviceIdResourcesHotspotWalledGardenGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static addHotspotServerApiV1MikrotikDeviceIdHotspotServerPost(
        deviceId: string,
        requestBody: HotspotServerCreate,
    ): CancelablePromise<any> {
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
    public static removeHotspotServerApiV1MikrotikDeviceIdHotspotServerDelete(
        deviceId: string,
        requestBody: HotspotNameDelete,
    ): CancelablePromise<any> {
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
    public static enableHotspotServerApiV1MikrotikDeviceIdHotspotServerNameEnablePost(
        deviceId: string,
        name: string,
    ): CancelablePromise<any> {
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
    public static disableHotspotServerApiV1MikrotikDeviceIdHotspotServerNameDisablePost(
        deviceId: string,
        name: string,
    ): CancelablePromise<any> {
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
    public static addHotspotUserApiV1MikrotikDeviceIdHotspotUserPost(
        deviceId: string,
        requestBody: HotspotUserCreate,
    ): CancelablePromise<any> {
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
    public static removeHotspotUserApiV1MikrotikDeviceIdHotspotUserDelete(
        deviceId: string,
        requestBody: HotspotNameDelete,
    ): CancelablePromise<any> {
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
    public static setHotspotUserApiV1MikrotikDeviceIdHotspotUserPatch(
        deviceId: string,
        requestBody: HotspotUserUpdate,
    ): CancelablePromise<any> {
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
    public static resetHotspotUserCountersApiV1MikrotikDeviceIdHotspotUserNameResetCountersPost(
        deviceId: string,
        name: string,
    ): CancelablePromise<any> {
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
    public static resetAllHotspotCountersApiV1MikrotikDeviceIdHotspotResetCountersAllPost(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static kickHotspotUserApiV1MikrotikDeviceIdHotspotKickPost(
        deviceId: string,
        requestBody: HotspotKickRequest,
    ): CancelablePromise<any> {
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
    public static addHotspotUserProfileApiV1MikrotikDeviceIdHotspotUserProfilePost(
        deviceId: string,
        requestBody: HotspotUserProfileCreate,
    ): CancelablePromise<any> {
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
    public static removeHotspotUserProfileApiV1MikrotikDeviceIdHotspotUserProfileDelete(
        deviceId: string,
        requestBody: HotspotNameDelete,
    ): CancelablePromise<any> {
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
    public static addHotspotIpBindingApiV1MikrotikDeviceIdHotspotIpBindingPost(
        deviceId: string,
        requestBody: HotspotIpBindingCreate,
    ): CancelablePromise<any> {
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
    public static removeHotspotIpBindingApiV1MikrotikDeviceIdHotspotIpBindingDelete(
        deviceId: string,
        requestBody: HotspotIpBindingDelete,
    ): CancelablePromise<any> {
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
    public static getPppActiveApiV1MikrotikDeviceIdResourcesPppActiveGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static addPppSecretApiV1MikrotikDeviceIdPppSecretPost(
        deviceId: string,
        requestBody: PppSecretCreate,
    ): CancelablePromise<any> {
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
    public static removePppSecretApiV1MikrotikDeviceIdPppSecretDelete(
        deviceId: string,
        requestBody: PppNameRequest,
    ): CancelablePromise<any> {
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
    public static setPppSecretApiV1MikrotikDeviceIdPppSecretPatch(
        deviceId: string,
        requestBody: PppSecretUpdate,
    ): CancelablePromise<any> {
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
    public static kickPppSessionApiV1MikrotikDeviceIdPppKickPost(
        deviceId: string,
        requestBody: PppKickRequest,
    ): CancelablePromise<any> {
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
    public static getTunnelServerStatusApiV1MikrotikDeviceIdResourcesTunnelTunnelTypeServerGet(
        deviceId: string,
        tunnelType: string,
    ): CancelablePromise<any> {
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
    public static setTunnelServerApiV1MikrotikDeviceIdTunnelTunnelTypeServerPatch(
        deviceId: string,
        tunnelType: string,
        requestBody: TunnelServerSet,
    ): CancelablePromise<any> {
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
    public static getPppoeServersApiV1MikrotikDeviceIdResourcesPppoeServersGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static addPppoeServerInstanceApiV1MikrotikDeviceIdPppoeServerInstancePost(
        deviceId: string,
        requestBody: PppoeServerCreate,
    ): CancelablePromise<any> {
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
    public static removePppoeServerInstanceApiV1MikrotikDeviceIdPppoeServerInstanceDelete(
        deviceId: string,
        requestBody: PppoeServerDelete,
    ): CancelablePromise<any> {
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
    public static getTunnelClientsApiV1MikrotikDeviceIdResourcesTunnelTunnelTypeClientsGet(
        deviceId: string,
        tunnelType: string,
    ): CancelablePromise<any> {
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
    public static addTunnelClientApiV1MikrotikDeviceIdTunnelClientPost(
        deviceId: string,
        requestBody: TunnelClientCreate,
    ): CancelablePromise<any> {
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
    public static removeTunnelClientApiV1MikrotikDeviceIdTunnelClientDelete(
        deviceId: string,
        requestBody: TunnelClientRequest,
    ): CancelablePromise<any> {
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
    public static manageTunnelClientApiV1MikrotikDeviceIdTunnelTunnelTypeClientNameActionPost(
        deviceId: string,
        tunnelType: string,
        name: string,
        action: string,
    ): CancelablePromise<any> {
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
    public static runCommandsApiV1MikrotikDeviceIdCommandsRunPost(
        deviceId: string,
        requestBody: CommandRunRequest,
    ): CancelablePromise<any> {
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
    public static getMonitoringApiV1MikrotikDeviceIdMonitoringPost(
        deviceId: string,
        requestBody: MonitoringRequest,
    ): CancelablePromise<any> {
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
    public static getHealthApiV1MikrotikDeviceIdHealthGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static pingToolApiV1MikrotikDeviceIdToolsPingPost(
        deviceId: string,
        requestBody: app__schemas__mikrotik__PingRequest,
    ): CancelablePromise<any> {
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
    public static tracerouteToolApiV1MikrotikDeviceIdToolsTraceroutePost(
        deviceId: string,
        requestBody: app__schemas__mikrotik__TracerouteRequest,
    ): CancelablePromise<any> {
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
    public static configTransactionApiV1MikrotikDeviceIdConfigTransactionPost(
        deviceId: string,
        requestBody: ConfigTransaction,
    ): CancelablePromise<any> {
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
    public static addOspfInstanceApiV1MikrotikDeviceIdOspfInstancePost(
        deviceId: string,
        requestBody: OspfInstanceCreate,
    ): CancelablePromise<any> {
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
    public static removeOspfInstanceApiV1MikrotikDeviceIdOspfInstanceDelete(
        deviceId: string,
        requestBody: OspfInstanceDelete,
    ): CancelablePromise<any> {
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
    public static addOspfAreaApiV1MikrotikDeviceIdOspfAreaPost(
        deviceId: string,
        requestBody: OspfAreaCreate,
    ): CancelablePromise<any> {
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
    public static addOspfInterfaceTemplateApiV1MikrotikDeviceIdOspfInterfaceTemplatePost(
        deviceId: string,
        requestBody: OspfInterfaceTemplateCreate,
    ): CancelablePromise<any> {
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
    public static addOspfNetworkApiV1MikrotikDeviceIdOspfNetworkPost(
        deviceId: string,
        requestBody: OspfNetworkCreate,
    ): CancelablePromise<any> {
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
    public static removeOspfNetworkApiV1MikrotikDeviceIdOspfNetworkDelete(
        deviceId: string,
        requestBody: OspfNetworkDelete,
    ): CancelablePromise<any> {
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
    public static saveConfigApiV1MikrotikDeviceIdConfigSavePost(
        deviceId: string,
    ): CancelablePromise<any> {
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
