import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
export function TopologyView() {
    const [topology, setTopology] = useState(null);
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const svgRef = useRef(null);
    const [panZoom, setPanZoom] = useState({ x: 0, y: 0, scale: 1 });
    useEffect(() => {
        loadTopology();
    }, []);
    async function loadTopology() {
        try {
            setLoading(true);
            const [topologyData, devicesData] = await Promise.all([
                api.getTopology().catch(() => null),
                api.devices.listDevices().catch(() => []),
            ]);
            setTopology(topologyData);
            setDevices(devicesData);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load topology');
        }
        finally {
            setLoading(false);
        }
    }
    const handleWheel = (e) => {
        e.preventDefault();
        setPanZoom(prev => ({
            ...prev,
            scale: Math.min(Math.max(prev.scale * (e.deltaY > 0 ? 0.9 : 1.1), 0.1), 5)
        }));
    };
    const handleMouseDown = (e) => {
        const startX = e.clientX - panZoom.x;
        const startY = e.clientY - panZoom.y;
        const handleMove = (e) => {
            setPanZoom(prev => ({
                ...prev,
                x: e.clientX - startX,
                y: e.clientY - startY
            }));
        };
        const handleUp = () => {
            window.removeEventListener('mousemove', handleMove);
            window.removeEventListener('mouseup', handleUp);
        };
        window.addEventListener('mousemove', handleMove);
        window.addEventListener('mouseup', handleUp);
    };
    if (loading) {
        return (_jsx("div", { className: "flex items-center justify-center h-64", children: _jsx("div", { className: "animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" }) }));
    }
    if (error) {
        return (_jsx("div", { className: "card", children: _jsxs("div", { className: "text-red-600", children: ["Error: ", error] }) }));
    }
    return (_jsxs("div", { className: "card h-[calc(100vh-200px)]", onWheel: handleWheel, children: [_jsxs("div", { className: "flex justify-between items-center mb-4", children: [_jsx("h2", { className: "text-xl font-semibold", children: "Network Topology" }), _jsx("div", { className: "flex gap-2", children: _jsx("button", { onClick: () => setPanZoom({ x: 0, y: 0, scale: 1 }), className: "btn btn-sm btn-secondary", children: "Reset View" }) })] }), _jsx("div", { className: "w-full h-full border border-gray-200 rounded-lg overflow-hidden bg-white", onMouseDown: handleMouseDown, children: _jsxs("svg", { width: "100%", height: "100%", viewBox: `0 0 1200 800`, style: {
                        transform: `translate(${panZoom.x}px, ${panZoom.y}px) scale(${panZoom.scale})`,
                        transformOrigin: '0 0'
                    }, children: [topology?.links?.map((link, i) => (_jsx("line", { x1: link.source_x || 100, y1: link.source_y || 100, x2: link.target_x || 200, y2: link.target_y || 200, stroke: "#9ca3af", strokeWidth: 2, strokeDasharray: "5,5" }, i))), devices.map((device, i) => {
                            const x = 100 + (i % 6) * 180;
                            const y = 100 + Math.floor(i / 6) * 150;
                            return (_jsxs("g", { transform: `translate(${x}, ${y})`, children: [_jsx("rect", { x: -60, y: -40, width: 120, height: 80, rx: 8, fill: device.status === 'active' ? '#dcfce7' : '#fee2e2', stroke: device.status === 'active' ? '#16a34a' : '#ef4444', strokeWidth: 2 }), _jsx("text", { x: 0, y: -15, textAnchor: "middle", fontSize: "12", fontWeight: "bold", fill: "#1f2937", children: device.hostname || device.id }), _jsx("text", { x: 0, y: 0, textAnchor: "middle", fontSize: "10", fill: "#6b7280", children: device.vendor?.toUpperCase() }), _jsx("text", { x: 0, y: 15, textAnchor: "middle", fontSize: "9", fill: "#6b7280", fontFamily: "monospace", children: device.management_address })] }, device.id));
                        }), devices.length === 0 && (_jsx("text", { x: "600", y: "400", textAnchor: "middle", fontSize: "16", fill: "#9ca3af", children: "No devices found" }))] }) })] }));
}
