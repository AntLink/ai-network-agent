import { useEffect, useState } from 'react';
import { api, type Gns3Config } from '../api/client';

export function Gns3LabManager() {
  const [config, setConfig] = useState<Gns3Config>({ controller_url: 'http://localhost:3080/v2', username: 'admin' });
  const [localConfig, setLocalConfig] = useState<{
    found: boolean;
    path?: string;
    auth_enabled: boolean;
    password_available: boolean;
  } | null>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any>(null);
  const [nodes, setNodes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'projects' | 'nodes' | 'links' | 'templates' | 'snapshots'>('projects');
  const [newProjectName, setNewProjectName] = useState('');

  useEffect(() => {
    bootstrapGns3();
  }, []);

  async function bootstrapGns3() {
    try {
      setLoading(true);
      const discovered = await api.gns3GetLocalConfig();
      setLocalConfig(discovered);
      const nextConfig = {
        ...config,
        controller_url: discovered.controller_url,
        username: discovered.username,
        password: undefined,
      };
      setConfig(nextConfig);
      const data = await api.gns3ListProjects(nextConfig);
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize GNS3');
    } finally {
      setLoading(false);
    }
  }

  async function testConnection(targetConfig: Gns3Config = config) {
    try {
      setLoading(true);
      const result = await api.gns3TestConnection(targetConfig);
      alert(`Connection OK: ${result.projects_count} projects found`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    } finally {
      setLoading(false);
    }
  }

  async function loadProjects() {
    try {
      setLoading(true);
      const data = await api.gns3ListProjects(config);
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  }

  async function createProject() {
    if (!newProjectName.trim()) return;
    try {
      const project = await api.gns3CreateProject(config, newProjectName);
      await loadProjects();
      setNewProjectName('');
      alert(`Project "${project.name}" created`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
    }
  }

  async function openProject(projectId: string) {
    try {
      await api.gns3OpenProject(projectId, config);
      await loadProjects();
      await selectProject(projectId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to open project');
    }
  }

  async function selectProject(projectId: string) {
    try {
      const project = await api.gns3GetProject(projectId, config);
      setSelectedProject(project);
      const nodesData = await api.gns3ListNodes(projectId, config);
      setNodes(nodesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load project');
    }
  }

  async function rebuildNode(nodeId: string) {
    if (!selectedProject) return;
    try {
      await api.gns3RebuildNode(selectedProject.project_id, nodeId, config, 'ide');
      await selectProject(selectedProject.project_id);
      alert('Node rebuilt successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rebuild node');
    }
  }

  async function setDiskInterface(nodeId: string, interfaceType: 'ide' | 'sata') {
    if (!selectedProject) return;
    try {
      await api.gns3SetDiskInterface(selectedProject.project_id, nodeId, config, interfaceType);
      await selectProject(selectedProject.project_id);
      alert(`Disk interface set to ${interfaceType}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set disk interface');
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'started': return <span className="badge badge-success">Running</span>;
      case 'stopped': return <span className="badge badge-warning">Stopped</span>;
      case 'suspended': return <span className="badge badge-warning">Suspended</span>;
      default: return <span className="badge badge-info">{status}</span>;
    }
  };

  return (
    <div>
      {/* Config Section */}
      <div className="card mb-4">
        <div className="card-header">
          <div>
            <h3 className="card-title">GNS3 Controller Connection</h3>
            {localConfig && (
              <p className="text-sm text-gray-500 mt-1">
                {localConfig.found
                  ? `Using local GNS3 config${localConfig.password_available ? ' with saved auth' : ''}.`
                  : 'Local GNS3 config not found, using manual settings.'}
              </p>
            )}
          </div>
          <button onClick={() => testConnection()} disabled={loading} className="btn btn-primary btn-sm">
            {loading ? 'Testing...' : 'Test Connection'}
          </button>
        </div>
        <div className="grid grid-cols-4 gap-4">
          <div className="form-group">
            <label className="label">Controller URL</label>
            <input
              type="text"
              value={config.controller_url}
              onChange={(e) => setConfig({...config, controller_url: e.target.value})}
              className="input"
              placeholder="http://localhost:3080/v2"
            />
          </div>
          <div className="form-group">
            <label className="label">Username</label>
            <input
              type="text"
              value={config.username}
              onChange={(e) => setConfig({...config, username: e.target.value})}
              className="input"
              placeholder="admin"
            />
          </div>
          <div className="form-group">
            <label className="label">Password</label>
            <input
              type="password"
              value={config.password || ''}
              onChange={(e) => setConfig({...config, password: e.target.value})}
              className="input"
              placeholder="Optional: backend auto-reads local GNS3 password"
            />
            <p className="text-xs text-gray-500 mt-1">
              Leave empty to use the saved password from gns3_server.ini.
            </p>
          </div>
          <div className="form-group">
            <label className="label">Local Config</label>
            <button onClick={bootstrapGns3} disabled={loading} className="btn btn-secondary w-full">
              {loading ? 'Loading...' : 'Use Local GNS3'}
            </button>
            {localConfig?.path && (
              <p className="text-xs text-gray-500 mt-1 font-mono">
                {localConfig.path}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {['projects', 'nodes', 'links', 'templates', 'snapshots'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={`tab ${activeTab === tab ? 'active' : ''}`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {activeTab === 'projects' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Projects ({projects.length})</h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="New project name..."
                className="input w-48"
              />
              <button onClick={async () => {
                if (!newProjectName.trim()) return;
                try {
                  const project = await api.gns3CreateProject(config, newProjectName);
                  await loadProjects();
                  setNewProjectName('');
                  alert(`Project "${project.name}" created`);
                } catch (err) {
                  setError(err instanceof Error ? err.message : 'Failed to create project');
                }
              }} className="btn btn-primary">Create</button>
            </div>
          </div>
          <div className="card overflow-hidden">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>ID</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {projects.map(project => (
                  <tr key={project.project_id} className={selectedProject?.project_id === project.project_id ? 'bg-blue-50' : ''}>
                    <td className="font-medium">{project.name}</td>
                    <td><span className={`badge ${project.status === 'opened' ? 'badge-success' : project.status === 'closed' ? 'badge-warning' : 'badge-error'}`}>{project.status}</span></td>
                    <td className="font-mono text-sm text-gray-500">{project.project_id.slice(0, 8)}...</td>
                    <td>
                      <div className="flex gap-2">
                        <button
                          onClick={() => openProject(project.project_id)}
                          className="btn btn-sm btn-primary"
                          disabled={project.status === 'opened'}
                        >
                          Open
                        </button>
                        {project.status === 'opened' && (
                          <button
                            onClick={() => selectProject(project.project_id)}
                            className="btn btn-sm btn-secondary"
                          >
                            View
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'nodes' && selectedProject && (
        <div>
          <h3 className="mb-4">Nodes in {selectedProject.name} ({nodes.length})</h3>
          <div className="card overflow-hidden">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Console</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {nodes.map(node => (
                  <tr key={node.node_id}>
                    <td className="font-medium">{node.name}</td>
                    <td className="text-sm text-gray-600">{node.node_type}</td>
                    <td>{getStatusBadge(node.status)}</td>
                    <td className="font-mono text-sm">
                      {node.console_host}:{node.console_port || 'N/A'}
                    </td>
                    <td>
                      <div className="flex gap-1">
                        {node.status !== 'started' && (
                          <button
                            onClick={async () => {
                              await api.gns3StartNode(selectedProject!.project_id, node.node_id, config);
                              await selectProject(selectedProject!.project_id);
                            }}
                            className="btn btn-sm btn-primary"
                          >
                            Start
                          </button>
                        )}
                        {node.status === 'started' && (
                          <button
                            onClick={async () => {
                              await api.gns3StopNode(selectedProject!.project_id, node.node_id, config);
                              await selectProject(selectedProject!.project_id);
                            }}
                            className="btn btn-sm btn-secondary"
                          >
                            Stop
                          </button>
                        )}
                        <button
                          onClick={() => rebuildNode(node.node_id)}
                          className="btn btn-sm btn-secondary"
                        >
                          Rebuild
                        </button>
                        <button
                          onClick={() => setDiskInterface(node.node_id, 'ide')}
                          className="btn btn-sm btn-secondary"
                        >
                          Set IDE
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'links' && selectedProject && (
        <div>
          <h3 className="mb-4">Links in {selectedProject.name}</h3>
          <div className="card">
            <div className="p-4 text-center text-gray-500">
              Links management coming soon
            </div>
          </div>
        </div>
      )}

      {activeTab === 'templates' && (
        <div>
          <h3 className="mb-4">Templates</h3>
          <div className="card">
            <p className="text-gray-500 text-sm mb-4">Templates loaded from GNS3 server</p>
            <div className="text-gray-500 text-sm">Template listing coming soon</div>
          </div>
        </div>
      )}

      {activeTab === 'snapshots' && selectedProject && (
        <div>
          <h3 className="mb-4">Snapshots for {selectedProject.name}</h3>
          <div className="card">
            <p className="text-gray-500 text-sm mb-4">Snapshot management coming soon</p>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
          <button onClick={() => setError(null)} className="ml-4 text-sm underline">Dismiss</button>
        </div>
      )}
    </div>
  );
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'started': return <span className="badge badge-success">Running</span>;
    case 'stopped': return <span className="badge badge-warning">Stopped</span>;
    case 'suspended': return <span className="badge badge-warning">Suspended</span>;
    default: return <span className="badge badge-info">{status}</span>;
  }
};
