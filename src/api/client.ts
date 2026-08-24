import { OpenAPI } from '../generated/core/OpenAPI';

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";

export type Gns3Config = {
  controller_url: string;
  compute_url?: string;
  username?: string;
  password?: string;
  verify_ssl?: boolean;
};

OpenAPI.BASE = API_BASE;
OpenAPI.WITH_CREDENTIALS = false;
OpenAPI.CREDENTIALS = 'omit';

/**
 * API Client for AI Network Agent
 * Uses fetch for direct HTTP calls with proper typing
 */
class ApiClient {
  private baseUrl: string;
  private requestTimeoutMs = 30000;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
    
    // Initialize service objects for backwards compatibility
    this.devices = {
      listDevices: () => this.listDevices(),
      getDevice: (deviceId: string) => this.getDevice(deviceId),
      identify: (deviceId: string) => this.identifyDevice(deviceId),
      facts: (deviceId: string) => this.getDeviceFacts(deviceId),
      interfaces: (deviceId: string) => this.getInterfaces(deviceId),
      routes: (deviceId: string) => this.getRoutes(deviceId),
      config: (deviceId: string) => this.getConfig(deviceId),
      vlans: (deviceId: string) => this.getVlans(deviceId),
      consoleExec: (deviceId: string, command: string) => this.consoleExec(deviceId, command),
      health: (deviceId: string) => this.getHealth(deviceId),
    };
    
    this.config = {
      createPlan: (plan: any) => this.configCreatePlan(plan),
      applyPlan: (planId: string, approvedBy: string) => this.configApplyPlan(planId, approvedBy),
      rollback: (rollback: any) => this.configRollback(rollback),
    };
  }

  // Service objects for backwards compatibility
  devices: {
    listDevices: () => Promise<any[]>;
    getDevice: (deviceId: string) => Promise<any>;
    identify: (deviceId: string) => Promise<any>;
    facts: (deviceId: string) => Promise<any>;
    interfaces: (deviceId: string) => Promise<any>;
    routes: (deviceId: string) => Promise<any>;
    config: (deviceId: string) => Promise<any>;
    vlans: (deviceId: string) => Promise<any>;
    consoleExec: (deviceId: string, command: string) => Promise<any>;
    health: (deviceId: string) => Promise<any>;
  };
  
  config: {
    createPlan: (plan: any) => Promise<any>;
    applyPlan: (planId: string, approvedBy: string) => Promise<any>;
    rollback: (rollback: any) => Promise<any>;
  };

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    let timeoutExpired = false;
    const timeoutId = window.setTimeout(() => {
      timeoutExpired = true;
      controller.abort();
    }, this.requestTimeoutMs);
    const incomingSignal = options.signal;

    const abortHandler = () => controller.abort();
    if (incomingSignal) {
      if (incomingSignal.aborted) {
        controller.abort();
      } else {
        incomingSignal.addEventListener('abort', abortHandler, { once: true });
      }
    }

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`API error ${response.status}: ${text}`);
      }

      if (response.status === 204) {
        return {} as T;
      }

      return response.json() as Promise<T>;
    } catch (err) {
      if (timeoutExpired || (err instanceof DOMException && err.name === 'AbortError')) {
        throw new Error(`Request timeout after ${Math.round(this.requestTimeoutMs / 1000)}s: ${path}`);
      }
      throw err;
    } finally {
      window.clearTimeout(timeoutId);
      if (incomingSignal) {
        incomingSignal.removeEventListener('abort', abortHandler);
      }
    }
  }

  // ========== DEVICES ==========

  async listDevices() {
    return this.request<any[]>('/devices');
  }

  async getDevice(deviceId: string) {
    return this.request<any>(`/devices/${deviceId}`);
  }

  async identifyDevice(deviceId: string) {
    return this.request<any>(`/devices/${deviceId}/identify`);
  }

  async getDeviceFacts(deviceId: string) {
    return this.request<any>(`/devices/${deviceId}/facts`);
  }

  async getInterfaces(deviceId: string) {
    return this.request<any>(`/devices/${deviceId}/interfaces`);
  }

  async getRoutes(deviceId: string) {
    return this.request<any>(`/devices/${deviceId}/routes`);
  }

  async getConfig(deviceId: string) {
    return this.request<any>(`/devices/${deviceId}/config`);
  }

  async getVlans(deviceId: string) {
    return this.request<any>(`/devices/${deviceId}/vlans`);
  }

  async consoleExec(deviceId: string, command: string) {
    return this.request<any>(`/devices/${deviceId}/console/exec`, {
      method: 'POST',
      body: JSON.stringify({ command }),
    });
  }

  async getHealth(deviceId: string) {
    return this.request<any>(`/devices/${deviceId}/health`);
  }

  // ========== CISCO SPECIFIC ==========

  async ciscoGetVersion(deviceId: string) {
    return this.request<any>(`/cisco/${deviceId}/resources/version`);
  }

  async ciscoGetInterfaces(deviceId: string) {
    return this.request<any>(`/cisco/${deviceId}/resources/interfaces`);
  }

  async ciscoGetInterfacesDetail(deviceId: string) {
    return this.request<any>(`/cisco/${deviceId}/resources/interfaces-detail`);
  }

  async ciscoGetRoutes(deviceId: string) {
    return this.request<any>(`/cisco/${deviceId}/resources/routes`);
  }

  async ciscoGetArp(deviceId: string) {
    return this.request<any>(`/cisco/${deviceId}/resources/arp`);
  }

  async ciscoGetCpuMemory(deviceId: string) {
    return this.request<any>(`/cisco/${deviceId}/resources/cpu-memory`);
  }

  async ciscoGetAcls(deviceId: string) {
    return this.request<any>(`/cisco/${deviceId}/resources/acls`);
  }

  async ciscoGetCdpNeighbors(deviceId: string) {
    return this.request<any>(`/cisco/${deviceId}/resources/cdp-neighbors`);
  }

  async ciscoGetNatTranslations(deviceId: string) {
    return this.request<any>(`/cisco/${deviceId}/resources/nat-translations`);
  }

  async ciscoGetLogs(deviceId: string) {
    return this.request<any>(`/cisco/${deviceId}/resources/logs`);
  }

  // ========== GNS3 ==========

  async gns3GetLocalConfig() {
    return this.request<{
      found: boolean;
      path?: string;
      controller_url: string;
      username: string;
      auth_enabled: boolean;
      password_available: boolean;
    }>('/gns3/local-config');
  }

  async gns3TestConnection(config: Gns3Config) {
    return this.request<any>('/gns3/test-connection', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3ListProjects(config: Gns3Config) {
    return this.request<any>('/gns3/projects', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3GetProject(projectId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3CreateProject(config: Gns3Config, name: string, path?: string) {
    return this.request<any>('/gns3/projects/create', {
      method: 'POST',
      body: JSON.stringify({ ...config, name, path }),
    });
  }

  async gns3OpenProject(projectId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/open`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3CloseProject(projectId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/close`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3DeleteProject(projectId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}`, {
      method: 'DELETE',
      body: JSON.stringify(config),
    });
  }

  async gns3ListNodes(projectId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/nodes`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3CreateNode(projectId: string, config: Gns3Config, nodeDef: any) {
    return this.request<any>(`/gns3/projects/${projectId}/nodes/create`, {
      method: 'POST',
      body: JSON.stringify({ ...config, node_def: nodeDef }),
    });
  }

  async gns3StartNode(projectId: string, nodeId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/nodes/${nodeId}/start`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3StopNode(projectId: string, nodeId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/nodes/${nodeId}/stop`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3RestartNode(projectId: string, nodeId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/nodes/${nodeId}/restart`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3DeleteNode(projectId: string, nodeId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/nodes/${nodeId}`, {
      method: 'DELETE',
      body: JSON.stringify(config),
    });
  }

  async gns3GetNodeConsole(projectId: string, nodeId: string) {
    return this.request<any>(`/gns3/projects/${projectId}/nodes/${nodeId}/console`);
  }

  async gns3RebuildNode(projectId: string, nodeId: string, config: Gns3Config, diskInterface: string) {
    return this.request<any>(`/gns3/projects/${projectId}/nodes/${nodeId}/rebuild`, {
      method: 'POST',
      body: JSON.stringify({ ...config, disk_interface: diskInterface }),
    });
  }

  async gns3SetDiskInterface(projectId: string, nodeId: string, config: Gns3Config, interfaceType: string) {
    return this.request<any>(`/gns3/projects/${projectId}/nodes/${nodeId}/disk-interface`, {
      method: 'POST',
      body: JSON.stringify({ ...config, interface: interfaceType }),
    });
  }

  async gns3UpdateNodeProperties(projectId: string, nodeId: string, config: Gns3Config, properties: any) {
    return this.request<any>(`/gns3/projects/${projectId}/nodes/${nodeId}/properties`, {
      method: 'POST',
      body: JSON.stringify({ ...config, properties }),
    });
  }

  async gns3ListLinks(projectId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/links`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3CreateLink(projectId: string, config: Gns3Config, nodes: any[]) {
    return this.request<any>(`/gns3/projects/${projectId}/links/create`, {
      method: 'POST',
      body: JSON.stringify({ ...config, nodes }),
    });
  }

  async gns3DeleteLink(projectId: string, linkId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/links/${linkId}`, {
      method: 'DELETE',
      body: JSON.stringify(config),
    });
  }

  async gns3ListTemplates(config: Gns3Config) {
    return this.request<any>('/gns3/templates', {
      method: 'GET',
    });
  }

  async gns3UpdateTemplate(templateId: string, config: Gns3Config, properties: any) {
    return this.request<any>(`/gns3/templates/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify({ ...config, properties }),
    });
  }

  async gns3ListSnapshots(projectId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/snapshots`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async gns3CreateSnapshot(projectId: string, config: Gns3Config, name: string) {
    return this.request<any>(`/gns3/projects/${projectId}/snapshots/create`, {
      method: 'POST',
      body: JSON.stringify({ ...config, name }),
    });
  }

  async gns3RestoreSnapshot(projectId: string, snapshotId: string, config: Gns3Config) {
    return this.request<any>(`/gns3/projects/${projectId}/snapshots/${snapshotId}/restore`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // ========== MIKROTIK ==========

  async mikrotikHealth(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/health`);
  }

  async mikrotikSystemIdentity(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/system/identity`);
  }

  async mikrotikSystemClock(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/system/clock`);
  }

  async mikrotikIpAddressList(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/ip/address`);
  }

  async mikrotikResourceIpAddresses(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/ip-addresses`);
  }

  async mikrotikResourceBridges(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/bridges`);
  }

  async mikrotikResourceBridgePorts(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/bridge-ports`);
  }

  async mikrotikResourceDhcpServers(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/dhcp-servers`);
  }

  async mikrotikResourceDhcpLeases(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/dhcp-leases`);
  }

  async mikrotikResourceStaticRoutes(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/static-routes`);
  }

  async mikrotikResourceFirewallNat(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/firewall/nat`);
  }

  async mikrotikResourceFirewallFilter(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/firewall/filter`);
  }

  async mikrotikResourceOspf(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/ospf`);
  }

  async mikrotikResourceBgp(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/bgp`);
  }

  async mikrotikIpRouteList(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/ip/route`);
  }

  async mikrotikInterfaceList(deviceId: string) {
    return this.request<any>(`/mikrotik/${deviceId}/resources/interfaces`);
  }

  async mikrotikPing(deviceId: string, address: string, count: number = 3) {
    return this.request<any>(`/mikrotik/${deviceId}/tools/ping`, {
      method: 'POST',
      body: JSON.stringify({ address, count }),
    });
  }

  // ========== MONITORING ==========

  async getMonitoring(deviceId: string, metrics?: string[]) {
    return this.request<any>(`/monitoring/${deviceId}`, {
      method: 'POST',
      body: JSON.stringify({ metrics: metrics || ["cpu", "memory", "disk", "temperature"] }),
    });
  }

  // ========== CONFIG ==========

  async configCreatePlan(plan: any) {
    return this.request<any>('/config/plan', {
      method: 'POST',
      body: JSON.stringify(plan),
    });
  }

  async configListPlans() {
    return this.request<any>('/config/plans');
  }

  async configGetPlan(planId: string) {
    return this.request<any>(`/config/plans/${planId}`);
  }

  async configApplyPlan(planId: string, approvedBy: string) {
    return this.request<any>('/config/apply', {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId, approved_by: approvedBy }),
    });
  }

  async configRollback(rollback: any) {
    return this.request<any>('/config/rollback', {
      method: 'POST',
      body: JSON.stringify(rollback),
    });
  }

  async policyCheck(payload: {
    device_id: string;
    operation: string;
    risk_level: string;
    plan_id?: string;
    approved_by?: string;
  }) {
    return this.request<any>('/policy/check', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // ========== TOPOLOGY ==========

  async getTopology() {
    return this.request<any>('/topology');
  }

  async getAuditLog(limit: number = 100) {
    return this.request<any>(`/audit?limit=${limit}`);
  }
}

export const api = new ApiClient();

export function setAuthToken(token: string) {
  // For future authentication support
}

export function setBaseUrl(url: string) {
  // For runtime base URL override
  OpenAPI.BASE = url;
}

export { ApiClient };
export default api;
