import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Card, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { formatDate, cn } from '../lib/utils'
import { Search, Filter, Globe, ChevronLeft, ChevronRight, Code } from 'lucide-react'
import toast from 'react-hot-toast'

interface Endpoint {
  id: string
  name: string
  method: string
  path: string
  full_url: string | null
  host: string | null
  status_code: number | null
  source_website: string | null
  discovered_at: string
  project_id: string
  run_id: string | null
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

const methodColors: Record<string, 'success' | 'destructive' | 'warning' | 'info' | 'secondary' | 'default'> = {
  GET: 'success',
  POST: 'warning',
  PUT: 'info',
  PATCH: 'info',
  DELETE: 'destructive',
  HEAD: 'secondary',
  OPTIONS: 'secondary',
}

export function EndpointsPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [methodFilter, setMethodFilter] = useState<string>('all')
  const [hostFilter, setHostFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const { data, isLoading } = useQuery({
    queryKey: ['endpoints', { search, method: methodFilter, host: hostFilter, page }],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      if (search) params.append('search', search)
      if (methodFilter !== 'all') params.append('method', methodFilter)
      if (hostFilter !== 'all') params.append('host', hostFilter)
      const response = await api.get<PaginatedResponse<Endpoint>>(`/endpoints?${params}`)
      return response.data
    },
  })

  const endpoints = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = data?.total_pages ?? 0

  // Get unique hosts for filter
  const { data: allEndpoints } = useQuery({
    queryKey: ['endpoints', 'all-hosts'],
    queryFn: async () => {
      const response = await api.get<{ items: Endpoint[] }>('/endpoints?page_size=1000')
      return response.data.items
    },
    staleTime: 5 * 60 * 1000,
  })

  const hosts = [...new Set((allEndpoints?.map(e => e.host).filter((h): h is string => Boolean(h)) || []))].sort()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">API Endpoints</h1>
          <p className="text-muted-foreground mt-1">Explore discovered API endpoints</p>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search endpoints..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select
              value={methodFilter}
              onChange={(e) => setMethodFilter(e.target.value)}
              className="w-full sm:w-40"
            >
              <option value="all">All Methods</option>
              {['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'].map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </Select>
            <Select
              value={hostFilter}
              onChange={(e) => setHostFilter(e.target.value)}
              className="w-full sm:w-56"
            >
              <option value="all">All Hosts</option>
              {hosts.map(h => (
                <option key={h} value={h}>{h}</option>
              ))}
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Endpoints Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : endpoints.length === 0 ? (
            <div className="text-center py-12">
              <Globe className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium mb-2">No endpoints found</h3>
              <p className="text-muted-foreground mb-4">
                {search || methodFilter !== 'all' || hostFilter !== 'all'
                  ? 'Try adjusting your search or filters'
                  : 'Run a discovery to find API endpoints'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-4 font-medium text-muted-foreground">Endpoint</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Method</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Path</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden md:table-cell">Host</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Status</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden lg:table-cell">Source</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Discovered</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {endpoints.map((endpoint: Endpoint) => (
                    <tr key={endpoint.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors cursor-pointer"
                      onClick={() => navigate(`/endpoints/${endpoint.id}`)}>
                    <td className="p-4">
                      <p className="font-medium">{endpoint.name}</p>
                      {endpoint.full_url && (
                        <p className="text-sm text-muted-foreground truncate max-w-xs mt-1">{endpoint.full_url}</p>
                      )}
                    </td>
                    <td className="p-4">
                      <Badge variant={methodColors[endpoint.method] || 'default'}>
                        {endpoint.method}
                      </Badge>
                    </td>
                    <td className="p-4 font-mono text-sm">{endpoint.path}</td>
                    <td className="p-4 hidden md:table-cell text-sm text-muted-foreground truncate max-w-xs">
                      {endpoint.host || '—'}
                    </td>
                    <td className="p-4">
                      {endpoint.status_code ? (
                        <Badge variant={endpoint.status_code >= 200 && endpoint.status_code < 300 ? 'success' : 'destructive'}>
                          {endpoint.status_code}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="p-4 hidden lg:table-cell text-sm text-muted-foreground truncate max-w-xs">
                      {endpoint.source_website || '—'}
                    </td>
                    <td className="p-4 text-sm text-muted-foreground">{formatDate(endpoint.discovered_at)}</td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button variant="ghost" size="icon" asChild>
                          <a href={endpoint.full_url || '#'} target="_blank" rel="noopener noreferrer">
                            <Globe className="h-4 w-4" />
                          </a>
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => {
                          navigator.clipboard.writeText(endpoint.path)
                          toast.success('Path copied')
                        }}>
                          <Code className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-border p-4">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} endpoints
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}