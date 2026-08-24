import { useState } from 'react';
import { DeviceList } from './components/DeviceList';
import { DeviceDetail } from './components/DeviceDetail';
import { Gns3LabManager } from './components/Gns3LabManager';
import { TopologyView } from './components/TopologyView';
import { ConfigManager } from './components/ConfigManager';
import { MonitoringDashboard } from './components/MonitoringDashboard';
import './index.css';

type View = 'devices' | 'device-detail' | 'gns3' | 'topology' | 'config' | 'monitoring';

type NavigationItem = {
  id: Exclude<View, 'device-detail'>;
  label: string;
  code: string;
  description: string;
};

type ToastKind = 'info' | 'success' | 'error';

type Toast = {
  id: number;
  message: string;
  kind: ToastKind;
  phase: 'enter' | 'shown' | 'exit';
};

function App() {
  const [view, setView] = useState<View>('devices');
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailLoadingMessage, setDetailLoadingMessage] = useState<string>('Memuat detail device...');
  const [toasts, setToasts] = useState<Toast[]>([]);

  const navigation: NavigationItem[] = [
    { id: 'devices', label: 'Devices', code: 'DEV', description: 'Inventory & access' },
    { id: 'gns3', label: 'GNS3 Labs', code: 'LAB', description: 'Controller workspace' },
    { id: 'topology', label: 'Topology', code: 'MAP', description: 'Network graph' },
    { id: 'config', label: 'Config', code: 'CFG', description: 'Plan & apply' },
    { id: 'monitoring', label: 'Monitoring', code: 'MON', description: 'Health telemetry' },
  ];

  const activeNavigation = navigation.find((item) => item.id === view);
  const viewTitle = view.replace('-', ' ');

  const pushToast = (message: string, kind: ToastKind = 'info') => {
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

  const handleDeviceClick = (deviceId: string) => {
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

  const handleNavigate = (nextView: NavigationItem['id']) => {
    setSelectedDevice(null);
    setDetailLoading(false);
    setDetailLoadingMessage('Memuat detail device...');
    setView(nextView);
  };

  return (
    <div className="app-shell min-h-screen">
      <header className="topbar sticky top-0 z-30">
        <div className="topbar-inner">
          <div className="brand-block">
            <div className="brand-mark">NA</div>
            <div>
              <p className="eyebrow">AI Network Agent</p>
              <h1>Network Control Center</h1>
            </div>
          </div>

          <div className="topbar-status">
            <span className="signal-dot"></span>
            <span>Development build</span>
          </div>
        </div>

        <nav className="topnav" aria-label="Primary navigation">
          {navigation.map((item) => {
            const active = view === item.id || (view === 'device-detail' && item.id === 'devices');

            return (
              <button
                key={item.id}
                onClick={() => handleNavigate(item.id)}
                className={`nav-pill ${active ? 'active' : ''}`}
              >
                <span className="nav-code">{item.code}</span>
                <span>
                  <span className="nav-label">{item.label}</span>
                  <span className="nav-description">{item.description}</span>
                </span>
              </button>
            );
          })}
        </nav>
      </header>

      <main className="workspace">
        <section className="hero-panel">
          <div>
            <p className="eyebrow">Current workspace</p>
            <h2 className="capitalize">{viewTitle}</h2>
            <p>{activeNavigation?.description || 'Device inspection and operational context'}</p>
          </div>

          <div className="hero-grid">
            <div>
              <span>Mode</span>
              <strong>Safe Ops</strong>
            </div>
            <div>
              <span>Stack</span>
              <strong>Cisco / MikroTik / GNS3</strong>
            </div>
            <div>
              <span>Workflow</span>
              <strong>Plan - Verify - Apply</strong>
            </div>
          </div>
        </section>

        <div className="content-panel">
          {view === 'devices' && <DeviceList onDeviceClick={handleDeviceClick} />}
          {view === 'device-detail' && selectedDevice && (
            <DeviceDetail
              deviceId={selectedDevice}
              onBack={handleBackToDevices}
              onLoadStateChange={(loading, message) => {
                setDetailLoading(loading);
                if (message) {
                  setDetailLoadingMessage(message);
                }
              }}
              onNotify={(message, kind = 'info') => pushToast(message, kind)}
            />
          )}
          {view === 'gns3' && <Gns3LabManager />}
          {view === 'topology' && <TopologyView />}
          {view === 'config' && <ConfigManager />}
          {view === 'monitoring' && <MonitoringDashboard />}
        </div>
      </main>

      {view === 'device-detail' && detailLoading && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/45 px-4 backdrop-blur-sm">
          <div className="rounded-[1.5rem] border border-white/20 bg-white/90 px-5 py-5 shadow-2xl">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-slate-200 border-t-teal-600" />
          </div>
        </div>
      )}

      <div className="fixed right-4 top-4 z-50 flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-3">
        {toasts.map((toast) => {
          const tone =
            toast.kind === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
              : toast.kind === 'error'
                ? 'border-rose-200 bg-rose-50 text-rose-900'
                : 'border-sky-200 bg-sky-50 text-sky-900';

          return (
            <div
              key={toast.id}
              className={`toast-shell rounded-2xl border px-4 py-3 shadow-xl backdrop-blur ${tone} toast-${toast.phase}`}
            >
              <div className="flex items-start gap-3">
                <div className="toast-icon mt-0.5 h-2.5 w-2.5 rounded-full bg-current" />
                <div className="min-w-0 flex-1">
                  <p className="text-[0.7rem] font-black uppercase tracking-[0.2em] opacity-70">
                    {toast.kind}
                  </p>
                  <p className="mt-1 text-sm font-medium leading-6">{toast.message}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default App;
