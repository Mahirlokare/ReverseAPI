import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Card, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { formatDate, cn } from '../lib/utils'
import { Search, Code, Download, ChevronLeft, ChevronRight, Eye, Play, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

interface Client {
  id: string
  name: string
  language: string
  version: string
  file_count: number
  validation_status: string | null
  source_capture_id: string | null
  run_id: string | null
  project_id: string
  ai_provider: string | null
  model: string | null
  created_at: string
  updated_at: string
}

interface ClientFile {
  id: string
  client_id: string
  file_path: string
  file_name: string
  content: string | null
  size: number | null
  mime_type: string | null
  created_at: string
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

const languageColors: Record<string, string> = {
  python: 'bg-blue-500/10 text-blue-500',
  javascript: 'bg-yellow-500/10 text-yellow-500',
  typescript: 'bg-blue-500/10 text-blue-500',
  go: 'bg-cyan-500/10 text-cyan-500',
  java: 'bg-red-500/10 text-red-500',
  csharp: 'bg-purple-500/10 text-purple-500',
  php: 'bg-indigo-500/10 text-indigo-500',
  ruby: 'bg-red-500/10 text-red-500',
  c: 'bg-gray-500/10 text-gray-500',
  powershell: 'bg-blue-500/10 text-blue-500',
}

export function ClientsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [languageFilter, setLanguageFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const { data, isLoading } = useQuery({
    queryKey: ['clients', { search, language: languageFilter, page }],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      if (search) params.append('search', search)
      if (languageFilter !== 'all') params.append('language', languageFilter)
      const response = await api.get<PaginatedResponse<Client>>(`/clients?${params}`)
      return response.data
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/clients/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      toast.success('Client deleted')
    },
    onError: () => toast.error('Failed to delete client'),
  })

  const clients = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = data?.total_pages ?? 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Generated Clients</h1>
          <p className="text-muted-foreground mt-1">View and manage generated API clients</p>
        </div>
        <Button variant="outline" asChild>
          <a href="/projects/new">
            <Code className="h-4 w-4 mr-2" />
            Generate New Client
          </a>
        </Button>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search clients..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select
              value={languageFilter}
              onChange={(e) => setLanguageFilter(e.target.value)}
              className="w-full sm:w-48"
            >
              <option value="all">All Languages</option>
              {Object.keys(languageColors).map(lang => (
                <option key={lang} value={lang}>{lang.charAt(0).toUpperCase() + lang.slice(1)}</option>
              ))}
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Clients Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : clients.length === 0 ? (
            <div className="text-center py-12">
              <Code className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium mb-2">No clients generated</h3>
              <p className="text-muted-foreground mb-4">
                {search || languageFilter !== 'all'
                  ? 'Try adjusting your search or filters'
                  : 'Run a discovery to generate API clients'}
              </p>
              <Button asChild>
                <a href="/projects/new">Start Discovery</a>
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-4 font-medium text-muted-foreground">Client</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Language</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Version</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Files</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Validation</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden lg:table-cell">AI Provider</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Created</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {clients.map((client: Client) => (
                    <tr key={client.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors cursor-pointer"
                      onClick={() => navigate(`/clients/${client.id}`)}>
                    <td className="p-4">
                      <p className="font-medium">{client.name}</p>
                      <p className="text-sm text-muted-foreground">Project: {client.project_id.slice(0, 8)}</p>
                    </td>
                    <td className="p-4">
                      <span className={cn('px-2 py-0.5 rounded text-xs font-medium', languageColors[client.language] || 'bg-muted text-muted-foreground')}>
                        {client.language.charAt(0).toUpperCase() + client.language.slice(1)}
                      </span>
                    </td>
                    <td className="p-4 text-sm text-muted-foreground">{client.version}</td>
                    <td className="p-4 text-sm text-muted-foreground">{client.file_count}</td>
                    <td className="p-4">
                      <Badge
                        variant={
                          client.validation_status === 'passed' ? 'success' :
                          client.validation_status === 'failed' ? 'destructive' :
                          'secondary'
                        }
                      >
                        {client.validation_status || 'Pending'}
                      </Badge>
                    </td>
                    <td className="p-4 hidden lg:table-cell text-sm text-muted-foreground">
                      {client.ai_provider ? `${client.ai_provider}${client.model ? ` (${client.model})` : ''}` : '—'}
                    </td>
                    <td className="p-4 text-sm text-muted-foreground">{formatDate(client.created_at)}</td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button variant="ghost" size="icon" onClick={() => navigate(`/clients/${client.id}`)} title="View Details">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => {}} title="Download ZIP">
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => {}} title="Execute Client" disabled={client.validation_status !== 'passed'}>
                          <Play className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => {
                          if (confirm('Delete this client?')) deleteMutation.mutate(client.id)
                        }} title="Delete">
                          <Trash2 className="h-4 w-4 text-destructive" />
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
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} clients
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
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