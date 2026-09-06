import useSWR from 'swr'
import type { ApiResponse } from 'src/types/network'
import type { DeployExecutionResult, DeployMode, DeployPreview, DeployTarget } from 'src/types/deploy'

export function buildDeployPreview(input: {
  title: string
  mode: DeployMode
  risk?: 'low' | 'medium' | 'high'
  requiresApproval?: boolean
  requiresBackup?: boolean
  target: DeployTarget
  steps: string[]
}): DeployPreview {
  return {
    id: `deploy-${Date.now()}`,
    title: input.title,
    mode: input.mode,
    risk: input.risk ?? 'low',
    requiresApproval: input.requiresApproval ?? input.mode !== 'lab',
    requiresBackup: input.requiresBackup ?? input.mode !== 'lab',
    steps: input.steps,
    targetCount: input.target.nodes.length,
    summary: `${input.target.projectName} / ${input.target.nodes.length} node(s) / ${input.mode.toUpperCase()} mode`,
  }
}

export async function simulateDeployExecution(preview: DeployPreview): Promise<DeployExecutionResult> {
  return {
    id: preview.id,
    status: 'queued',
    message: `Deploy preview ready for ${preview.title}`,
    startedAt: new Date().toISOString(),
  }
}

export function useDeployPreview(input?: {
  title: string
  mode: DeployMode
  target: DeployTarget
  steps: string[]
}) {
  return useSWR<ApiResponse<DeployPreview>>(
    input ? ['deploy-preview', input.title, input.mode, input.target.projectId] : null,
    async () => ({
      status: 200,
      data: buildDeployPreview({
        title: input!.title,
        mode: input!.mode,
        target: input!.target,
        steps: input!.steps,
      }),
    })
  )
}

