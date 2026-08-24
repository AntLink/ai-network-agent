import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { api } from '../api/client';
export function ConfigManager() {
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState('');
    const [commands, setCommands] = useState('');
    const [verifyCommands, setVerifyCommands] = useState('');
    const [saveOnSuccess, setSaveOnSuccess] = useState(false);
    const [description, setDescription] = useState('');
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('create');
    useEffect(() => {
        loadDevices();
        loadPlans();
    }, []);
    async function loadDevices() {
        try {
            const data = await api.devices.listDevices();
            setDevices(data);
        }
        catch (err) {
            console.error('Failed to load devices:', err);
        }
    }
    async function createPlan() {
        if (!selectedDevice || !commands.trim()) {
            setError('Please select a device and enter commands');
            return;
        }
        try {
            setLoading(true);
            const verify = verifyCommands.trim().split('\n')
                .filter(v => v.trim())
                .map(v => {
                const [command, expect] = v.split('|').map(s => s.trim());
                return { command, expect: expect || undefined };
            });
            const plan = {
                device_id: selectedDevice,
                commands: commands.trim().split('\n').filter(c => c.trim()),
                verify,
                save_on_success: saveOnSuccess,
                description: description || undefined,
            };
            const result = await api.configCreatePlan(plan);
            setPlans(prev => [...prev.filter(p => p.plan_id !== result.plan_id), result]);
            setCommands('');
            setVerifyCommands('');
            setDescription('');
            setActiveTab('plans');
            alert(`Plan created: ${result.plan_id}`);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create plan');
        }
        finally {
            setLoading(false);
        }
    }
    async function applyPlan(planId) {
        try {
            setLoading(true);
            const plan = await api.configGetPlan(planId);
            const approvedBy = window.prompt(`Approve ${plan.risk_level} risk plan ${planId}. Enter approver name:`);
            if (!approvedBy?.trim()) {
                setError('Approval name is required');
                return;
            }
            const policy = await api.policyCheck({
                device_id: plan.device_id,
                operation: 'apply',
                risk_level: plan.risk_level,
                plan_id: plan.plan_id,
                approved_by: approvedBy.trim(),
            });
            if (!policy.allowed) {
                setError(policy.reason || 'Policy denied this plan');
                return;
            }
            const result = await api.configApplyPlan(planId, approvedBy.trim());
            await loadPlans();
            alert(`Plan applied: ${result.status}`);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to apply plan');
        }
        finally {
            setLoading(false);
        }
    }
    async function loadPlans() {
        try {
            const data = await api.configListPlans();
            setPlans(data.plans || []);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load plans');
        }
    }
    const getRiskBadge = (risk) => {
        switch (risk) {
            case 'LOW': return _jsx("span", { className: "badge badge-success", children: "LOW" });
            case 'MEDIUM': return _jsx("span", { className: "badge badge-info", children: "MEDIUM" });
            case 'HIGH': return _jsx("span", { className: "badge badge-warning", children: "HIGH" });
            case 'CRITICAL': return _jsx("span", { className: "badge badge-error", children: "CRITICAL" });
            default: return _jsx("span", { className: "badge badge-info", children: risk || 'UNKNOWN' });
        }
    };
    return (_jsxs("div", { children: [_jsxs("div", { className: "tabs", children: [_jsx("button", { onClick: () => setActiveTab('create'), className: `tab ${activeTab === 'create' ? 'active' : ''}`, children: "Create Plan" }), _jsx("button", { onClick: () => { setActiveTab('plans'); loadPlans(); }, className: `tab ${activeTab === 'plans' ? 'active' : ''}`, children: "Plans" })] }), activeTab === 'create' && (_jsxs("div", { className: "card", children: [_jsxs("div", { className: "grid grid-cols-2 gap-4 mb-4", children: [_jsxs("div", { className: "form-group", children: [_jsx("label", { className: "label", children: "Device" }), _jsxs("select", { value: selectedDevice, onChange: (e) => setSelectedDevice(e.target.value), className: "input", children: [_jsx("option", { value: "", children: "Select device..." }), devices.map(d => (_jsxs("option", { value: d.id, children: [d.hostname || d.id, " (", d.vendor, ")"] }, d.id)))] })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "label", children: "Save on Success" }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx("input", { type: "checkbox", checked: saveOnSuccess, onChange: (e) => setSaveOnSuccess(e.target.checked), className: "w-4 h-4 text-blue-600 rounded" }), _jsx("label", { className: "text-sm", children: "Save config after successful apply" })] })] })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "label", children: "Commands (one per line)" }), _jsx("textarea", { value: commands, onChange: (e) => setCommands(e.target.value), className: "input font-mono text-sm", rows: 8, placeholder: "interface GigabitEthernet0/1\n description UPLINK_TO_CORE\n no shutdown" })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "label", children: "Verify Commands (optional, one per line, use | for expected output)" }), _jsx("textarea", { value: verifyCommands, onChange: (e) => setVerifyCommands(e.target.value), className: "input font-mono text-sm", rows: 4, placeholder: "show interface GigabitEthernet0/1 | up\nshow run interface GigabitEthernet0/1 | description UPLINK_TO_CORE" })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "label", children: "Description" }), _jsx("input", { type: "text", value: description, onChange: (e) => setDescription(e.target.value), className: "input", placeholder: "Optional description..." })] }), _jsxs("div", { className: "flex gap-2", children: [_jsx("button", { onClick: createPlan, disabled: loading || !selectedDevice, className: "btn btn-primary", children: loading ? 'Creating...' : 'Create Plan' }), _jsx("button", { onClick: () => { setCommands(''); setVerifyCommands(''); setDescription(''); }, className: "btn btn-secondary", children: "Clear" })] }), error && _jsx("div", { className: "mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700", children: error })] })), activeTab === 'plans' && (_jsxs("div", { className: "card", children: [_jsxs("div", { className: "flex justify-between items-center mb-4", children: [_jsx("h3", { children: "Plans" }), _jsx("button", { onClick: loadPlans, disabled: loading, className: "btn btn-sm btn-secondary", children: "Refresh" })] }), plans.length === 0 ? (_jsx("p", { className: "text-gray-500 text-sm", children: "No in-memory plans on the backend." })) : (_jsx("div", { className: "overflow-x-auto", children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "Plan" }), _jsx("th", { children: "Device" }), _jsx("th", { children: "Risk" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "Commands" }), _jsx("th", { children: "Action" })] }) }), _jsx("tbody", { children: plans.map((plan) => (_jsxs("tr", { children: [_jsx("td", { className: "font-mono", children: plan.plan_id }), _jsx("td", { className: "font-mono text-sm", children: plan.device_id }), _jsx("td", { children: getRiskBadge(plan.risk_level) }), _jsx("td", { children: plan.status }), _jsx("td", { className: "font-mono text-sm", children: plan.commands?.length || 0 }), _jsx("td", { children: _jsx("button", { onClick: () => applyPlan(plan.plan_id), disabled: loading || plan.status !== 'planned', className: "btn btn-sm btn-primary", children: "Apply" }) })] }, plan.plan_id))) })] }) })), error && _jsx("div", { className: "mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700", children: error })] }))] }));
}
