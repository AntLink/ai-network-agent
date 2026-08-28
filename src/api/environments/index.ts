import useSWR from 'swr'
import { backendOrMock, loadBackendDashboardSummary, loadBackendSettings, loadGns3Projects } from 'src/api/network/backend-client'
import type { ApiResponse, DashboardSummary, Gns3Project, NetworkSettings } from 'src/types/network'
import type { EnvironmentProfile, EnvironmentProjectBinding, EnvironmentType, EnvironmentWorkflowStep } from 'src/types/environment'

export const environmentProfiles: EnvironmentProfile[] = [
  {
    id: 'lab',
    name: 'Lab',
    description: 'Exploration and topology drafting environment.',
    engine: 'gns3',
    color: 'text-sky-500',
    badge: 'bg-sky-500/10 text-sky-600 border-sky-500/20',
    policy: {
      approvalRequired: false,
      backupRequired: false,
      rollbackEnabled: true,
      destructiveCommandsAllowed: true,
      postChangeValidation: true,
    },
  },
  {
    id: 'staging',
    name: 'Staging',
    description: 'Production-like validation before rollout.',
    engine: 'containerlab',
    color: 'text-amber-500',
    badge: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
    policy: {
      approvalRequired: true,
      backupRequired: true,
      rollbackEnabled: true,
      destructiveCommandsAllowed: false,
      postChangeValidation: true,
    },
  },
  {
    id: 'production',
    name: 'Production',
    description: 'Live network devices and guarded execution.',
    color: 'text-emerald-500',
    badge: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
    policy: {
      approvalRequired: true,
      backupRequired: true,
      rollbackEnabled: true,
      destructiveCommandsAllowed: false,
      postChangeValidation: true,
    },
  },
]

const PROJECT_ENVIRONMENT_MAP: Record<string, EnvironmentType> = {
  'a6967457-f60e-4752-be8f-6b66e925245c': 'lab',
  '5845909f-e540-4011-a7f7-86112c1a539d': 'lab',
  'static-routing-lab': 'lab',
}

export function resolveEnvironmentFromProjectId(projectId?: string): EnvironmentType {
  if (!projectId) {
    return 'lab'
  }
  return PROJECT_ENVIRONMENT_MAP[projectId] ?? 'lab'
}

export function getEnvironmentProfile(environment: EnvironmentType): EnvironmentProfile {
  return environmentProfiles.find((profile) => profile.id === environment) ?? environmentProfiles[0]
}

export function getEnvironmentWorkflow(environment: EnvironmentType): EnvironmentWorkflowStep[] {
  const baseSteps: EnvironmentWorkflowStep[] = [
    { key: 'discover', title: 'Discover', status: 'success', description: 'Resolve project inventory and live nodes.' },
    { key: 'plan', title: 'Plan', status: 'running', description: 'Build execution plan and confirm target scope.' },
    { key: 'dry-run', title: 'Dry Run', status: 'pending', description: 'Preview commands without applying changes.' },
    { key: 'approve', title: 'Approval', status: 'pending', description: 'Wait for user approval when required.' },
    { key: 'backup', title: 'Backup', status: 'pending', description: 'Create pre-change safety snapshot.' },
    { key: 'execute', title: 'Execute', status: 'pending', description: 'Apply the approved change to target devices.' },
    { key: 'verify', title: 'Verify', status: 'pending', description: 'Check post-change health and connectivity.' },
  ]

  if (environment === 'lab') {
    return baseSteps.map((step, index) => ({
      ...step,
      status: index < 2 ? 'success' : index === 2 ? 'running' : 'pending',
    }))
  }

  if (environment === 'staging') {
    return baseSteps.map((step, index) => ({
      ...step,
      status: index < 3 ? 'success' : index === 3 ? 'running' : 'pending',
    }))
  }

  return baseSteps.map((step, index) => ({
    ...step,
    status: index < 1 ? 'success' : index === 1 ? 'running' : 'pending',
  }))
}

export async function loadEnvironmentSummary(): Promise<DashboardSummary> {
  return backendOrMock(loadBackendDashboardSummary, '/api/network/dashboard').then((response) => response.data)
}

export async function loadEnvironmentSettings(): Promise<NetworkSettings> {
  return backendOrMock(loadBackendSettings, '/api/network/settings').then((response) => response.data)
}

export async function loadEnvironmentProjects(): Promise<Gns3Project[]> {
  const response = await backendOrMock(loadGns3Projects, '/api/network/gns3')
  const data = response.data as unknown
  if (Array.isArray(data)) {
    return data as Gns3Project[]
  }
  const record = data && typeof data === 'object' ? (data as Record<string, unknown>) : {}
  return Array.isArray(record.projects) ? (record.projects as Gns3Project[]) : []
}

export async function loadProjectBinding(projectId?: string): Promise<EnvironmentProjectBinding | null> {
  if (!projectId) return null
  const projects = await loadEnvironmentProjects()
  const project = projects.find((item) => item.id === projectId)
  if (!project) return null
  return {
    projectId: project.id,
    projectName: project.name,
    environment: resolveEnvironmentFromProjectId(project.id),
    lastSyncedAt: project.created,
  }
}

export function useEnvironmentProfiles() {
  return useSWR<ApiResponse<EnvironmentProfile[]>>('environment-profiles', async () => ({
    status: 200,
    data: environmentProfiles,
  }))
}

export function useEnvironmentWorkflow(environment: EnvironmentType = 'lab') {
  return useSWR<ApiResponse<EnvironmentWorkflowStep[]>>(['environment-workflow', environment], async () => ({
    status: 200,
    data: getEnvironmentWorkflow(environment),
  }))
}

export function useEnvironmentOverview(projectId?: string) {
  return useSWR<ApiResponse<{
    summary: DashboardSummary
    settings: NetworkSettings
    projects: Gns3Project[]
    activeBinding: EnvironmentProjectBinding | null
  }>>(
    ['environment-overview', projectId ?? 'default'],
    async () => {
      const [summary, settings, projects, activeBinding] = await Promise.all([
        loadEnvironmentSummary(),
        loadEnvironmentSettings(),
        loadEnvironmentProjects(),
        loadProjectBinding(projectId),
      ])

      return {
        status: 200,
        data: {
          summary,
          settings,
          projects,
          activeBinding,
        },
      }
    }
  )
}
