import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { formatDate, formatFileSize } from '../lib/utils'
import { Search, Database, Download, Upload, Trash2, ChevronLeft, ChevronRight, Eye, Code } from 'lucide-react'
import toast from 'react-hot-toast'

interface Capture {
  id: string
  file_path: string
  file_size: number | null
  request_count: number
  host_distribution: Record<string, number> | null
  methods_distribution: Record<string, number> | null
  target_domain: string | null
  is_sanitized: boolean
  compatibility_status: string | null
  project_id: string
  run_id: string | null
  created_at: string
  updated_at: string
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export function CapturesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const { data, isLoading } = useQuery({
    queryKey: ['captures', { search, page }],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      if (search) params.append('search', search)
      const response = await api.get<PaginatedResponse<Capture>>(`/captures?${params}`)
      return response.data
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/captures/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['captures'] })
      toast.success('Capture deleted')
    },
    onError: () => toast.error('Failed to delete capture'),
  })

  const captures = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = data?.total_pages ?? 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Captures & HAR</h1>
          <p className="text-muted-foreground mt-1">Manage captured network traffic</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => {}} disabled>
            <Upload className="h-4 w-4 mr-2" />
            Import HAR
          </Button>
        </div>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search captures..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Captures Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : captures.length === 0 ? (
            <div className="text-center py-12">
              <Database className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium mb-2">No captures found</h3>
              <p className="text-muted-foreground mb-4">
                {search ? 'Try adjusting your search' : 'Run a discovery to capture network traffic'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-4 font-medium text-muted-foreground">Capture</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden md:table-cell">Domain</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Requests</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Size</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden lg:table-cell">Methods</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Sanitized</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Compatibility</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Date</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {captures.map((capture: Capture) => (
                    <tr key={capture.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                      <td className="p-4">
                        <p className="font-medium truncate max-w-xs">{capture.file_path.split('/').pop()}</p>
                        {capture.run_id && (
                          <p className="text-xs text-muted-foreground">Run: {capture.run_id.slice(0, 8)}</p>
                        )}
                      </td>
                      <td className="p-4 hidden md:table-cell text-sm text-muted-foreground">
                        {capture.target_domain || '—'}
                      </td>
                      <td className="p-4 text-sm text-muted-foreground">{capture.request_count.toLocaleString()}</td>
                      <td className="p-4 text-sm text-muted-foreground">
                        {capture.file_size ? formatFileSize(capture.file_size) : '—'}
                      </td>
                      <td className="p-4 hidden lg:table-cell">
                        {capture.methods_distribution && (
                          <div className="flex gap-1 flex-wrap">
                            {Object.entries(capture.methods_distribution).map(([method, count]) => (
                              <Badge key={method} variant="outline" className="text-xs">{method}: {String(count)}</Badge>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="p-4">
                        <Badge variant={capture.is_sanitized ? 'success' : 'outline'}>
                          {capture.is_sanitized ? 'Yes' : 'No'}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <Badge variant="outline">{capture.compatibility_status || 'Unknown'}</Badge>
                      </td>
                      <td className="p-4 text-sm text-muted-foreground">{formatDate(capture.created_at)}</td>
                      <td className="p-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="ghost" size="icon" onClick={() => {}} title="Download">
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => navigate(`/captures/${capture.id}`)} title="View Details">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => {}} title="Engineer Client" disabled={!capture.compatibility_status || capture.compatibility_status === 'incompatible'}>
                            <Code className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => {
                            if (confirm('Delete this capture?')) deleteMutation.mutate(capture.id)
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
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} captures
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