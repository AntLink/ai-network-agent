/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AccessPortSet } from '../models/AccessPortSet';
import type { AclApply } from '../models/AclApply';
import type { AclCreate } from '../models/AclCreate';
import type { AclDelete } from '../models/AclDelete';
import type { app__schemas__cisco__DnsSet } from '../models/app__schemas__cisco__DnsSet';
import type { app__schemas__cisco__PingRequest } from '../models/app__schemas__cisco__PingRequest';
import type { app__schemas__cisco__StaticRouteCreate } from '../models/app__schemas__cisco__StaticRouteCreate';
import type { app__schemas__cisco__StaticRouteDelete } from '../models/app__schemas__cisco__StaticRouteDelete';
import type { app__schemas__cisco__TracerouteRequest } from '../models/app__schemas__cisco__TracerouteRequest';
import type { app__schemas__cisco__VlanCreate } from '../models/app__schemas__cisco__VlanCreate';
import type { BannerSet } from '../models/BannerSet';
import type { CommandRunRequest } from '../models/CommandRunRequest';
import type { ConfigTransaction } from '../models/ConfigTransaction';
import type { InterfaceAddressSet } from '../models/InterfaceAddressSet';
import type { InterfaceDescriptionSet } from '../models/InterfaceDescriptionSet';
import type { InterfaceMtuSet } from '../models/InterfaceMtuSet';
import type { LocalUserCreate } from '../models/LocalUserCreate';
import type { NetmikoConfigPush } from '../models/NetmikoConfigPush';
import type { NtpServerAdd } from '../models/NtpServerAdd';
import type { SubinterfaceCreate } from '../models/SubinterfaceCreate';
import type { SviSet } from '../models/SviSet';
import type { TrunkPortSet } from '../models/TrunkPortSet';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CiscoService {
    /**
     * Get Version
     * @param deviceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getVersionApiV1CiscoDeviceIdResourcesVersionGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getInterfacesApiV1CiscoDeviceIdResourcesInterfacesGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getInterfacesDetailApiV1CiscoDeviceIdResourcesInterfacesDetailGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getRoutesApiV1CiscoDeviceIdResourcesRoutesGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getArpApiV1CiscoDeviceIdResourcesArpGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getCpuMemoryApiV1CiscoDeviceIdResourcesCpuMemoryGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getAclsApiV1CiscoDeviceIdResourcesAclsGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getCdpNeighborsApiV1CiscoDeviceIdResourcesCdpNeighborsGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getNatTranslationsApiV1CiscoDeviceIdResourcesNatTranslationsGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static getLogsApiV1CiscoDeviceIdResourcesLogsGet(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static setHostnameApiV1CiscoDeviceIdSystemHostnamePost(
        deviceId: string,
        requestBody: Record<string, any>,
    ): CancelablePromise<any> {
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
    public static setDnsApiV1CiscoDeviceIdSystemDnsPost(
        deviceId: string,
        requestBody: app__schemas__cisco__DnsSet,
    ): CancelablePromise<any> {
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
    public static addNtpServerApiV1CiscoDeviceIdSystemNtpPost(
        deviceId: string,
        requestBody: NtpServerAdd,
    ): CancelablePromise<any> {
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
    public static removeNtpServerApiV1CiscoDeviceIdSystemNtpServerDelete(
        deviceId: string,
        server: string,
    ): CancelablePromise<any> {
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
    public static setBannerApiV1CiscoDeviceIdSystemBannerPost(
        deviceId: string,
        requestBody: BannerSet,
    ): CancelablePromise<any> {
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
    public static createLocalUserApiV1CiscoDeviceIdUsersPost(
        deviceId: string,
        requestBody: LocalUserCreate,
    ): CancelablePromise<any> {
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
    public static deleteLocalUserApiV1CiscoDeviceIdUsersUsernameDelete(
        deviceId: string,
        username: string,
    ): CancelablePromise<any> {
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
    public static interfaceDescriptionApiV1CiscoDeviceIdInterfaceDescriptionPost(
        deviceId: string,
        requestBody: InterfaceDescriptionSet,
    ): CancelablePromise<any> {
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
    public static interfaceAddressApiV1CiscoDeviceIdInterfaceAddressPost(
        deviceId: string,
        requestBody: InterfaceAddressSet,
    ): CancelablePromise<any> {
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
    public static interfaceRemoveAddressApiV1CiscoDeviceIdInterfaceInterfaceAddressDelete(
        deviceId: string,
        _interface: string,
    ): CancelablePromise<any> {
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
    public static interfaceMtuApiV1CiscoDeviceIdInterfaceMtuPost(
        deviceId: string,
        requestBody: InterfaceMtuSet,
    ): CancelablePromise<any> {
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
    public static interfaceStateApiV1CiscoDeviceIdInterfaceNameActionPost(
        deviceId: string,
        name: string,
        action: string,
    ): CancelablePromise<any> {
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
    public static addStaticRouteApiV1CiscoDeviceIdStaticRoutePost(
        deviceId: string,
        requestBody: app__schemas__cisco__StaticRouteCreate,
    ): CancelablePromise<any> {
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
    public static removeStaticRouteApiV1CiscoDeviceIdStaticRouteDelete(
        deviceId: string,
        requestBody: app__schemas__cisco__StaticRouteDelete,
    ): CancelablePromise<any> {
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
    public static createAclApiV1CiscoDeviceIdAclPost(
        deviceId: string,
        requestBody: AclCreate,
    ): CancelablePromise<any> {
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
    public static deleteAclApiV1CiscoDeviceIdAclDelete(
        deviceId: string,
        requestBody: AclDelete,
    ): CancelablePromise<any> {
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
    public static applyAclApiV1CiscoDeviceIdAclApplyPost(
        deviceId: string,
        requestBody: AclApply,
    ): CancelablePromise<any> {
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
    public static unapplyAclApiV1CiscoDeviceIdAclUnapplyPost(
        deviceId: string,
        requestBody: AclApply,
    ): CancelablePromise<any> {
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
    public static createVlanApiV1CiscoDeviceIdL2VlanPost(
        deviceId: string,
        requestBody: app__schemas__cisco__VlanCreate,
    ): CancelablePromise<any> {
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
    public static deleteVlanApiV1CiscoDeviceIdL2VlanVlanIdDelete(
        deviceId: string,
        vlanId: number,
    ): CancelablePromise<any> {
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
    public static setAccessPortApiV1CiscoDeviceIdL2AccessPost(
        deviceId: string,
        requestBody: AccessPortSet,
    ): CancelablePromise<any> {
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
    public static setTrunkPortApiV1CiscoDeviceIdL2TrunkPost(
        deviceId: string,
        requestBody: TrunkPortSet,
    ): CancelablePromise<any> {
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
    public static createSubinterfaceApiV1CiscoDeviceIdL2SubinterfacePost(
        deviceId: string,
        requestBody: SubinterfaceCreate,
    ): CancelablePromise<any> {
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
    public static setSviApiV1CiscoDeviceIdL2SviPost(
        deviceId: string,
        requestBody: SviSet,
    ): CancelablePromise<any> {
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
    public static runCommandsApiV1CiscoDeviceIdCommandsRunPost(
        deviceId: string,
        requestBody: CommandRunRequest,
    ): CancelablePromise<any> {
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
    public static pingToolApiV1CiscoDeviceIdToolsPingPost(
        deviceId: string,
        requestBody: app__schemas__cisco__PingRequest,
    ): CancelablePromise<any> {
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
    public static tracerouteToolApiV1CiscoDeviceIdToolsTraceroutePost(
        deviceId: string,
        requestBody: app__schemas__cisco__TracerouteRequest,
    ): CancelablePromise<any> {
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
    public static saveConfigApiV1CiscoDeviceIdConfigSavePost(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static configTransactionApiV1CiscoDeviceIdConfigTransactionPost(
        deviceId: string,
        requestBody: ConfigTransaction,
    ): CancelablePromise<any> {
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
    public static backupConfigApiV1CiscoDeviceIdConfigBackupPost(
        deviceId: string,
    ): CancelablePromise<any> {
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
    public static netmikoConfigPushApiV1CiscoDeviceIdConfigPushPost(
        deviceId: string,
        requestBody: NetmikoConfigPush,
    ): CancelablePromise<any> {
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
    public static netmikoExecApiV1CiscoDeviceIdExecPost(
        deviceId: string,
        requestBody: CommandRunRequest,
    ): CancelablePromise<any> {
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
