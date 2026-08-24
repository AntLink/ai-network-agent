import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

export function TopologyView() {
  const [topology, setTopology] = useState<any>(null);
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load topology');
    } finally {
      setLoading(false);
    }
  }

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setPanZoom(prev => ({
      ...prev,
      scale: Math.min(Math.max(prev.scale * (e.deltaY > 0 ? 0.9 : 1.1), 0.1), 5)
    }));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    const startX = e.clientX - panZoom.x;
    const startY = e.clientY - panZoom.y;

    const handleMove = (e: MouseEvent) => {
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
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="card h-[calc(100vh-200px)]" onWheel={handleWheel}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Network Topology</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setPanZoom({ x: 0, y: 0, scale: 1 })}
            className="btn btn-sm btn-secondary"
          >
            Reset View
          </button>
        </div>
      </div>

      <div
        className="w-full h-full border border-gray-200 rounded-lg overflow-hidden bg-white"
        onMouseDown={handleMouseDown}
      >
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 1200 800`}
          style={{
            transform: `translate(${panZoom.x}px, ${panZoom.y}px) scale(${panZoom.scale})`,
            transformOrigin: '0 0'
          }}
        >
          {/* Draw links first */}
          {topology?.links?.map((link: any, i: number) => (
            <line
              key={i}
              x1={link.source_x || 100}
              y1={link.source_y || 100}
              x2={link.target_x || 200}
              y2={link.target_y || 200}
              stroke="#9ca3af"
              strokeWidth={2}
              strokeDasharray="5,5"
            />
          ))}

          {/* Draw devices as nodes */}
          {devices.map((device, i) => {
            const x = 100 + (i % 6) * 180;
            const y = 100 + Math.floor(i / 6) * 150;
            return (
              <g key={device.id} transform={`translate(${x}, ${y})`}>
                <rect
                  x={-60}
                  y={-40}
                  width={120}
                  height={80}
                  rx={8}
                  fill={device.status === 'active' ? '#dcfce7' : '#fee2e2'}
                  stroke={device.status === 'active' ? '#16a34a' : '#ef4444'}
                  strokeWidth={2}
                />
                <text
                  x={0}
                  y={-15}
                  textAnchor="middle"
                  fontSize="12"
                  fontWeight="bold"
                  fill="#1f2937"
                >
                  {device.hostname || device.id}
                </text>
                <text
                  x={0}
                  y={0}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#6b7280"
                >
                  {device.vendor?.toUpperCase()}
                </text>
                <text
                  x={0}
                  y={15}
                  textAnchor="middle"
                  fontSize="9"
                  fill="#6b7280"
                  fontFamily="monospace"
                >
                  {device.management_address}
                </text>
              </g>
            );
          })}
          {devices.length === 0 && (
            <text
              x="600"
              y="400"
              textAnchor="middle"
              fontSize="16"
              fill="#9ca3af"
            >
              No devices found
            </text>
          )}
        </svg>
      </div>
    </div>
  );
}