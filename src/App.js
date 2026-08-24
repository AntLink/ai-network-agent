import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { DeviceList } from './components/DeviceList';
import { DeviceDetail } from './components/DeviceDetail';
import { Gns3LabManager } from './components/Gns3LabManager';
import { TopologyView } from './components/TopologyView';
import { ConfigManager } from './components/ConfigManager';
import { MonitoringDashboard } from './components/MonitoringDashboard';
import './index.css';
function App() {
    const [view, setView] = useState('devices');
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);
    const [detailLoadingMessage, setDetailLoadingMessage] = useState('Memuat detail device...');
    const [toasts, setToasts] = useState([]);
    const navigation = [
        { id: 'devices', label: 'Devices', code: 'DEV', description: 'Inventory & access' },
        { id: 'gns3', label: 'GNS3 Labs', code: 'LAB', description: 'Controller workspace' },
        { id: 'topology', label: 'Topology', code: 'MAP', description: 'Network graph' },
        { id: 'config', label: 'Config', code: 'CFG', description: 'Plan & apply' },
        { id: 'monitoring', label: 'Monitoring', code: 'MON', description: 'Health telemetry' },
    ];
    const activeNavigation = navigation.find((item) => item.id === view);
    const viewTitle = view.replace('-', ' ');
    const pushToast = (message, kind = 'info') => {
        const id = Date.now() + Math.floor(Math.random() * 1000);
        setToasts((current) => [...current, { id, message, kind, phase: 'enter' }]);
        window.setTimeout(() => {
            setToasts((current) => current.map((toast) => (toast.id === id ? { ...toast, phase: 'shown' } : toast)));
        }, 20);
        window.setTimeout(() => {
            setToasts((current) => current.map((toast) => (toast.id === id ? { ...toast, phase: 'exit' } : toast)));
        }, 3200);
        window.setTimeout(() => {
            setToasts((current) => current.filter((toast) => toast.id !== id));
        }, 3800);
    };
    const handleDeviceClick = (deviceId) => {
        setSelectedDevice(deviceId);
        setDetailLoading(true);
        setDetailLoadingMessage(`Membuka detail ${deviceId}...`);
        setView('device-detail');
    };
    const handleBackToDevices = () => {
        setSelectedDevice(null);
        setDetailLoading(false);
        setDetailLoadingMessage('Memuat detail device...');
        setView('devices');
    };
    const handleNavigate = (nextView) => {
        setSelectedDevice(null);
        setDetailLoading(false);
        setDetailLoadingMessage('Memuat detail device...');
        setView(nextView);
    };
    return (_jsxs("div", { className: "app-shell min-h-screen", children: [_jsxs("header", { className: "topbar sticky top-0 z-30", children: [_jsxs("div", { className: "topbar-inner", children: [_jsxs("div", { className: "brand-block", children: [_jsx("div", { className: "brand-mark", children: "NA" }), _jsxs("div", { children: [_jsx("p", { className: "eyebrow", children: "AI Network Agent" }), _jsx("h1", { children: "Network Control Center" })] })] }), _jsxs("div", { className: "topbar-status", children: [_jsx("span", { className: "signal-dot" }), _jsx("span", { children: "Development build" })] })] }), _jsx("nav", { className: "topnav", "aria-label": "Primary navigation", children: navigation.map((item) => {
                            const active = view === item.id || (view === 'device-detail' && item.id === 'devices');
                            return (_jsxs("button", { onClick: () => handleNavigate(item.id), className: `nav-pill ${active ? 'active' : ''}`, children: [_jsx("span", { className: "nav-code", children: item.code }), _jsxs("span", { children: [_jsx("span", { className: "nav-label", children: item.label }), _jsx("span", { className: "nav-description", children: item.description })] })] }, item.id));
                        }) })] }), _jsxs("main", { className: "workspace", children: [_jsxs("section", { className: "hero-panel", children: [_jsxs("div", { children: [_jsx("p", { className: "eyebrow", children: "Current workspace" }), _jsx("h2", { className: "capitalize", children: viewTitle }), _jsx("p", { children: activeNavigation?.description || 'Device inspection and operational context' })] }), _jsxs("div", { className: "hero-grid", children: [_jsxs("div", { children: [_jsx("span", { children: "Mode" }), _jsx("strong", { children: "Safe Ops" })] }), _jsxs("div", { children: [_jsx("span", { children: "Stack" }), _jsx("strong", { children: "Cisco / MikroTik / GNS3" })] }), _jsxs("div", { children: [_jsx("span", { children: "Workflow" }), _jsx("strong", { children: "Plan - Verify - Apply" })] })] })] }), _jsxs("div", { className: "content-panel", children: [view === 'devices' && _jsx(DeviceList, { onDeviceClick: handleDeviceClick }), view === 'device-detail' && selectedDevice && (_jsx(DeviceDetail, { deviceId: selectedDevice, onBack: handleBackToDevices, onLoadStateChange: (loading, message) => {
                                    setDetailLoading(loading);
                                    if (message) {
                                        setDetailLoadingMessage(message);
                                    }
                                }, onNotify: (message, kind = 'info') => pushToast(message, kind) })), view === 'gns3' && _jsx(Gns3LabManager, {}), view === 'topology' && _jsx(TopologyView, {}), view === 'config' && _jsx(ConfigManager, {}), view === 'monitoring' && _jsx(MonitoringDashboard, {})] })] }), view === 'device-detail' && detailLoading && (_jsx("div", { className: "fixed inset-0 z-40 flex items-center justify-center bg-slate-950/45 px-4 backdrop-blur-sm", children: _jsx("div", { className: "rounded-[1.5rem] border border-white/20 bg-white/90 px-5 py-5 shadow-2xl", children: _jsx("div", { className: "h-12 w-12 animate-spin rounded-full border-4 border-slate-200 border-t-teal-600" }) }) })), _jsx("div", { className: "fixed right-4 top-4 z-50 flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-3", children: toasts.map((toast) => {
                    const tone = toast.kind === 'success'
                        ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
                        : toast.kind === 'error'
                            ? 'border-rose-200 bg-rose-50 text-rose-900'
                            : 'border-sky-200 bg-sky-50 text-sky-900';
                    return (_jsx("div", { className: `toast-shell rounded-2xl border px-4 py-3 shadow-xl backdrop-blur ${tone} toast-${toast.phase}`, children: _jsxs("div", { className: "flex items-start gap-3", children: [_jsx("div", { className: "toast-icon mt-0.5 h-2.5 w-2.5 rounded-full bg-current" }), _jsxs("div", { className: "min-w-0 flex-1", children: [_jsx("p", { className: "text-[0.7rem] font-black uppercase tracking-[0.2em] opacity-70", children: toast.kind }), _jsx("p", { className: "mt-1 text-sm font-medium leading-6", children: toast.message })] })] }) }, toast.id));
                }) })] }));
}
export default App;
