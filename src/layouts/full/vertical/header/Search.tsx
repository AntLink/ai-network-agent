import { useMemo, useState } from 'react'
import { Search as SearchIcon } from 'lucide-react'
import SimpleBar from 'simplebar-react'
import { Link } from 'react-router'
import { Input } from '@/components/ui/input'
import { devices, labs } from 'src/api/network/network-data'
import SidebarContent from '../../vertical/sidebar/sidebaritems'
import type { ChildItem, MenuItem } from '../../vertical/sidebar/sidebaritems'

type SearchResult = {
  name: string
  url: string
  path: string
  description: string
}

function Search() {
  const [query, setQuery] = useState('')

  const results = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    if (!normalizedQuery) return []

    const navigationResults = searchItems(SidebarContent, normalizedQuery)
    const deviceResults: SearchResult[] = devices
      .filter((device) =>
        [device.hostname, device.managementIp, device.serial, device.model, device.platform, device.lab].some((value) =>
          value.toLowerCase().includes(normalizedQuery)
        )
      )
      .map((device) => ({
        name: device.hostname,
        url: `/devices/${device.id}`,
        path: `${device.vendor.toUpperCase()} / ${device.model}`,
        description: `${device.managementIp} / ${device.status}`,
      }))
    const labResults: SearchResult[] = labs
      .filter((lab) => [lab.name, lab.engine, lab.status].some((value) => value.toLowerCase().includes(normalizedQuery)))
      .map((lab) => ({
        name: lab.name,
        url: `/labs/${lab.id}`,
        path: `Lab / ${lab.engine}`,
        description: `${lab.nodes} nodes / ${lab.status}`,
      }))

    return [...deviceResults, ...labResults, ...navigationResults].slice(0, 12)
  }, [query])

  return (
    <div className="relative w-full">
      <div className="relative mx-auto flex w-xs items-center">
        <SearchIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search devices, IPs, labs, tasks..."
          className="rounded-lg pl-10!"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>
      <div className={`absolute start-0 top-11 z-10 w-full rounded-md border border-border bg-card shadow-md ${query ? 'block' : 'hidden'}`}>
        <SimpleBar className="h-72 p-4">
          {results.length ? (
            results.map((item) => (
              <Link
                key={`${item.url}-${item.name}`}
                to={item.url}
                onClick={() => setQuery('')}
                className="mb-1.5 flex w-full items-center gap-2 overflow-hidden rounded-md bg-input/30 p-2 text-sm font-medium last:mb-0 hover:bg-primary/5 hover:text-primary"
              >
                <SearchIcon width={18} height={18} />
                <div className="min-w-0 ps-2">
                  <h5 className="mb-1 text-sm">{item.name}</h5>
                  <span className="block max-w-60 truncate text-xs text-muted-foreground">
                    {item.path} / {item.description}
                  </span>
                </div>
              </Link>
            ))
          ) : (
            <div className="flex h-full items-center justify-center">
              <h1 className="text-sm font-medium">No results found</h1>
            </div>
          )}
        </SimpleBar>
      </div>
    </div>
  )
}

function searchItems(items: Array<MenuItem | ChildItem>, query: string, parentPath = ''): SearchResult[] {
  let results: SearchResult[] = []

  items.forEach((item) => {
    const heading = 'heading' in item ? item.heading : undefined
    const name = item.name ?? heading ?? ''
    const currentPath = parentPath ? `${parentPath} / ${name}` : name

    if (item.name && item.url && item.name.toLowerCase().includes(query)) {
      results.push({
        name: item.name,
        url: item.url,
        path: currentPath,
        description: item.url,
      })
    }

    if (item.items) {
      results = [...results, ...searchItems(item.items, query, currentPath)]
    }
  })

  return results
}

export default Search
