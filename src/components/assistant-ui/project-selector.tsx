import type { Gns3Project } from 'src/types/network'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'

export function ProjectSelector({
  projects,
  value,
  onValueChange,
}: {
  projects: Gns3Project[]
  value: string
  onValueChange: (value: string) => void
}) {
  const safeValue = value && ['all-projects', ...projects.map((project) => project.id)].includes(value) ? value : 'all-projects'

  return (
    <Select value={safeValue} onValueChange={(next) => onValueChange(next ?? 'all-projects')}>
      <SelectTrigger className="w-56">
        <SelectValue placeholder="Select project" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all-projects">All projects</SelectItem>
        {projects.map((project) => (
          <SelectItem key={project.id} value={project.id}>
            {project.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
