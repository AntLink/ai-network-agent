import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { api } from '../api/client';
export function Gns3LabManager() {
    const [config, setConfig] = useState({ controller_url: 'http://localhost:3080/v2', username: 'admin' });
    const [localConfig, setLocalConfig] = useState(null);
    const [projects, setProjects] = useState([]);
    const [selectedProject, setSelectedProject] = useState(null);
    const [nodes, setNodes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('projects');
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
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to initialize GNS3');
        }
        finally {
            setLoading(false);
        }
    }
    async function testConnection(targetConfig = config) {
        try {
            setLoading(true);
            const result = await api.gns3TestConnection(targetConfig);
            alert(`Connection OK: ${result.projects_count} projects found`);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Connection failed');
        }
        finally {
            setLoading(false);
        }
    }
    async function loadProjects() {
        try {
            setLoading(true);
            const data = await api.gns3ListProjects(config);
            setProjects(data);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load projects');
        }
        finally {
            setLoading(false);
        }
    }
    async function createProject() {
        if (!newProjectName.trim())
            return;
        try {
            const project = await api.gns3CreateProject(config, newProjectName);
            await loadProjects();
            setNewProjectName('');
            alert(`Project "${project.name}" created`);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create project');
        }
    }
    async function openProject(projectId) {
        try {
            await api.gns3OpenProject(projectId, config);
            await loadProjects();
            await selectProject(projectId);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to open project');
        }
    }
    async function selectProject(projectId) {
        try {
            const project = await api.gns3GetProject(projectId, config);
            setSelectedProject(project);
            const nodesData = await api.gns3ListNodes(projectId, config);
            setNodes(nodesData);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load project');
        }
    }
    async function rebuildNode(nodeId) {
        if (!selectedProject)
            return;
        try {
            await api.gns3RebuildNode(selectedProject.project_id, nodeId, config, 'ide');
            await selectProject(selectedProject.project_id);
            alert('Node rebuilt successfully');
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to rebuild node');
        }
    }
    async function setDiskInterface(nodeId, interfaceType) {
        if (!selectedProject)
            return;
        try {
            await api.gns3SetDiskInterface(selectedProject.project_id, nodeId, config, interfaceType);
            await selectProject(selectedProject.project_id);
            alert(`Disk interface set to ${interfaceType}`);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to set disk interface');
        }
    }
    const getStatusBadge = (status) => {
        switch (status) {
            case 'started': return _jsx("span", { className: "badge badge-success", children: "Running" });
            case 'stopped': return _jsx("span", { className: "badge badge-warning", children: "Stopped" });
            case 'suspended': return _jsx("span", { className: "badge badge-warning", children: "Suspended" });
            default: return _jsx("span", { className: "badge badge-info", children: status });
        }
    };
    return (_jsxs("div", { children: [_jsxs("div", { className: "card mb-4", children: [_jsxs("div", { className: "card-header", children: [_jsxs("div", { children: [_jsx("h3", { className: "card-title", children: "GNS3 Controller Connection" }), localConfig && (_jsx("p", { className: "text-sm text-gray-500 mt-1", children: localConfig.found
                                            ? `Using local GNS3 config${localConfig.password_available ? ' with saved auth' : ''}.`
                                            : 'Local GNS3 config not found, using manual settings.' }))] }), _jsx("button", { onClick: () => testConnection(), disabled: loading, className: "btn btn-primary btn-sm", children: loading ? 'Testing...' : 'Test Connection' })] }), _jsxs("div", { className: "grid grid-cols-4 gap-4", children: [_jsxs("div", { className: "form-group", children: [_jsx("label", { className: "label", children: "Controller URL" }), _jsx("input", { type: "text", value: config.controller_url, onChange: (e) => setConfig({ ...config, controller_url: e.target.value }), className: "input", placeholder: "http://localhost:3080/v2" })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "label", children: "Username" }), _jsx("input", { type: "text", value: config.username, onChange: (e) => setConfig({ ...config, username: e.target.value }), className: "input", placeholder: "admin" })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "label", children: "Password" }), _jsx("input", { type: "password", value: config.password || '', onChange: (e) => setConfig({ ...config, password: e.target.value }), className: "input", placeholder: "Optional: backend auto-reads local GNS3 password" }), _jsx("p", { className: "text-xs text-gray-500 mt-1", children: "Leave empty to use the saved password from gns3_server.ini." })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "label", children: "Local Config" }), _jsx("button", { onClick: bootstrapGns3, disabled: loading, className: "btn btn-secondary w-full", children: loading ? 'Loading...' : 'Use Local GNS3' }), localConfig?.path && (_jsx("p", { className: "text-xs text-gray-500 mt-1 font-mono", children: localConfig.path }))] })] })] }), _jsx("div", { className: "tabs", children: ['projects', 'nodes', 'links', 'templates', 'snapshots'].map(tab => (_jsx("button", { onClick: () => setActiveTab(tab), className: `tab ${activeTab === tab ? 'active' : ''}`, children: tab.charAt(0).toUpperCase() + tab.slice(1) }, tab))) }), activeTab === 'projects' && (_jsxs("div", { children: [_jsxs("div", { className: "flex justify-between items-center mb-4", children: [_jsxs("h3", { className: "text-lg font-semibold", children: ["Projects (", projects.length, ")"] }), _jsxs("div", { className: "flex gap-2", children: [_jsx("input", { type: "text", value: newProjectName, onChange: (e) => setNewProjectName(e.target.value), placeholder: "New project name...", className: "input w-48" }), _jsx("button", { onClick: async () => {
                                            if (!newProjectName.trim())
                                                return;
                                            try {
                                                const project = await api.gns3CreateProject(config, newProjectName);
                                                await loadProjects();
                                                setNewProjectName('');
                                                alert(`Project "${project.name}" created`);
                                            }
                                            catch (err) {
                                                setError(err instanceof Error ? err.message : 'Failed to create project');
                                            }
                                        }, className: "btn btn-primary", children: "Create" })] })] }), _jsx("div", { className: "card overflow-hidden", children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "Name" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "ID" }), _jsx("th", { children: "Actions" })] }) }), _jsx("tbody", { children: projects.map(project => (_jsxs("tr", { className: selectedProject?.project_id === project.project_id ? 'bg-blue-50' : '', children: [_jsx("td", { className: "font-medium", children: project.name }), _jsx("td", { children: _jsx("span", { className: `badge ${project.status === 'opened' ? 'badge-success' : project.status === 'closed' ? 'badge-warning' : 'badge-error'}`, children: project.status }) }), _jsxs("td", { className: "font-mono text-sm text-gray-500", children: [project.project_id.slice(0, 8), "..."] }), _jsx("td", { children: _jsxs("div", { className: "flex gap-2", children: [_jsx("button", { onClick: () => openProject(project.project_id), className: "btn btn-sm btn-primary", disabled: project.status === 'opened', children: "Open" }), project.status === 'opened' && (_jsx("button", { onClick: () => selectProject(project.project_id), className: "btn btn-sm btn-secondary", children: "View" }))] }) })] }, project.project_id))) })] }) })] })), activeTab === 'nodes' && selectedProject && (_jsxs("div", { children: [_jsxs("h3", { className: "mb-4", children: ["Nodes in ", selectedProject.name, " (", nodes.length, ")"] }), _jsx("div", { className: "card overflow-hidden", children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "Name" }), _jsx("th", { children: "Type" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "Console" }), _jsx("th", { children: "Actions" })] }) }), _jsx("tbody", { children: nodes.map(node => (_jsxs("tr", { children: [_jsx("td", { className: "font-medium", children: node.name }), _jsx("td", { className: "text-sm text-gray-600", children: node.node_type }), _jsx("td", { children: getStatusBadge(node.status) }), _jsxs("td", { className: "font-mono text-sm", children: [node.console_host, ":", node.console_port || 'N/A'] }), _jsx("td", { children: _jsxs("div", { className: "flex gap-1", children: [node.status !== 'started' && (_jsx("button", { onClick: async () => {
                                                                await api.gns3StartNode(selectedProject.project_id, node.node_id, config);
                                                                await selectProject(selectedProject.project_id);
                                                            }, className: "btn btn-sm btn-primary", children: "Start" })), node.status === 'started' && (_jsx("button", { onClick: async () => {
                                                                await api.gns3StopNode(selectedProject.project_id, node.node_id, config);
                                                                await selectProject(selectedProject.project_id);
                                                            }, className: "btn btn-sm btn-secondary", children: "Stop" })), _jsx("button", { onClick: () => rebuildNode(node.node_id), className: "btn btn-sm btn-secondary", children: "Rebuild" }), _jsx("button", { onClick: () => setDiskInterface(node.node_id, 'ide'), className: "btn btn-sm btn-secondary", children: "Set IDE" })] }) })] }, node.node_id))) })] }) })] })), activeTab === 'links' && selectedProject && (_jsxs("div", { children: [_jsxs("h3", { className: "mb-4", children: ["Links in ", selectedProject.name] }), _jsx("div", { className: "card", children: _jsx("div", { className: "p-4 text-center text-gray-500", children: "Links management coming soon" }) })] })), activeTab === 'templates' && (_jsxs("div", { children: [_jsx("h3", { className: "mb-4", children: "Templates" }), _jsxs("div", { className: "card", children: [_jsx("p", { className: "text-gray-500 text-sm mb-4", children: "Templates loaded from GNS3 server" }), _jsx("div", { className: "text-gray-500 text-sm", children: "Template listing coming soon" })] })] })), activeTab === 'snapshots' && selectedProject && (_jsxs("div", { children: [_jsxs("h3", { className: "mb-4", children: ["Snapshots for ", selectedProject.name] }), _jsx("div", { className: "card", children: _jsx("p", { className: "text-gray-500 text-sm mb-4", children: "Snapshot management coming soon" }) })] })), error && (_jsxs("div", { className: "mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700", children: [error, _jsx("button", { onClick: () => setError(null), className: "ml-4 text-sm underline", children: "Dismiss" })] }))] }));
}
const getStatusBadge = (status) => {
    switch (status) {
        case 'started': return _jsx("span", { className: "badge badge-success", children: "Running" });
        case 'stopped': return _jsx("span", { className: "badge badge-warning", children: "Stopped" });
        case 'suspended': return _jsx("span", { className: "badge badge-warning", children: "Suspended" });
        default: return _jsx("span", { className: "badge badge-info", children: status });
    }
};
