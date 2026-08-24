import { useState, useEffect } from 'react';
import { api } from '../api/client';

interface ConfigPlan {
  plan_id: string;
  device_id: string;
  commands: string[];
  verify: any[];
  save_on_success: boolean;
  description: string;
  risk_level: string;
  status: string;
  report?: any;
}

export function ConfigManager() {
  const [devices, setDevices] = useState<any[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [commands, setCommands] = useState<string>('');
  const [verifyCommands, setVerifyCommands] = useState<string>('');
  const [saveOnSuccess, setSaveOnSuccess] = useState(false);
  const [description, setDescription] = useState('');
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'create' | 'plans'>('create');

  useEffect(() => {
    loadDevices();
    loadPlans();
  }, []);

  async function loadDevices() {
    try {
      const data = await api.devices.listDevices();
      setDevices(data);
    } catch (err) {
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create plan');
    } finally {
      setLoading(false);
    }
  }

  async function applyPlan(planId: string) {
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply plan');
    } finally {
      setLoading(false);
    }
  }

  async function loadPlans() {
    try {
      const data = await api.configListPlans();
      setPlans(data.plans || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load plans');
    }
  }

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'LOW': return <span className="badge badge-success">LOW</span>;
      case 'MEDIUM': return <span className="badge badge-info">MEDIUM</span>;
      case 'HIGH': return <span className="badge badge-warning">HIGH</span>;
      case 'CRITICAL': return <span className="badge badge-error">CRITICAL</span>;
      default: return <span className="badge badge-info">{risk || 'UNKNOWN'}</span>;
    }
  };

  return (
    <div>
      <div className="tabs">
        <button
          onClick={() => setActiveTab('create')}
          className={`tab ${activeTab === 'create' ? 'active' : ''}`}
        >
          Create Plan
        </button>
        <button
          onClick={() => { setActiveTab('plans'); loadPlans(); }}
          className={`tab ${activeTab === 'plans' ? 'active' : ''}`}
        >
          Plans
        </button>
      </div>

      {activeTab === 'create' && (
        <div className="card">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="form-group">
              <label className="label">Device</label>
              <select
                value={selectedDevice}
                onChange={(e) => setSelectedDevice(e.target.value)}
                className="input"
              >
                <option value="">Select device...</option>
                {devices.map(d => (
                  <option key={d.id} value={d.id}>
                    {d.hostname || d.id} ({d.vendor})
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="label">Save on Success</label>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={saveOnSuccess}
                  onChange={(e) => setSaveOnSuccess(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <label className="text-sm">Save config after successful apply</label>
              </div>
            </div>
          </div>

          <div className="form-group">
            <label className="label">Commands (one per line)</label>
            <textarea
              value={commands}
              onChange={(e) => setCommands(e.target.value)}
              className="input font-mono text-sm"
              rows={8}
              placeholder="interface GigabitEthernet0/1
 description UPLINK_TO_CORE
 no shutdown"
          />
        </div>

        <div className="form-group">
          <label className="label">Verify Commands (optional, one per line, use | for expected output)</label>
          <textarea
            value={verifyCommands}
            onChange={(e) => setVerifyCommands(e.target.value)}
            className="input font-mono text-sm"
            rows={4}
            placeholder="show interface GigabitEthernet0/1 | up
show run interface GigabitEthernet0/1 | description UPLINK_TO_CORE"
          />
        </div>

        <div className="form-group">
          <label className="label">Description</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input"
            placeholder="Optional description..."
          />
        </div>

        <div className="flex gap-2">
          <button onClick={createPlan} disabled={loading || !selectedDevice} className="btn btn-primary">
            {loading ? 'Creating...' : 'Create Plan'}
          </button>
          <button onClick={() => { setCommands(''); setVerifyCommands(''); setDescription(''); }} className="btn btn-secondary">Clear</button>
        </div>

        {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">{error}</div>}
      </div>
      )}

      {activeTab === 'plans' && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3>Plans</h3>
            <button onClick={loadPlans} disabled={loading} className="btn btn-sm btn-secondary">
              Refresh
            </button>
          </div>
          {plans.length === 0 ? (
            <p className="text-gray-500 text-sm">No in-memory plans on the backend.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Plan</th>
                    <th>Device</th>
                    <th>Risk</th>
                    <th>Status</th>
                    <th>Commands</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {plans.map((plan: ConfigPlan) => (
                    <tr key={plan.plan_id}>
                      <td className="font-mono">{plan.plan_id}</td>
                      <td className="font-mono text-sm">{plan.device_id}</td>
                      <td>{getRiskBadge(plan.risk_level)}</td>
                      <td>{plan.status}</td>
                      <td className="font-mono text-sm">{plan.commands?.length || 0}</td>
                      <td>
                        <button
                          onClick={() => applyPlan(plan.plan_id)}
                          disabled={loading || plan.status !== 'planned'}
                          className="btn btn-sm btn-primary"
                        >
                          Apply
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">{error}</div>}
        </div>
      )}
    </div>
  );
}
