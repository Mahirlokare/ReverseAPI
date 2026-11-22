import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { NavLink, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { formatDate, cn } from '../lib/utils'
import { Plus, Search, Filter, MoreHorizontal, Edit, Trash2, Archive, Copy, ExternalLink, FolderKanban } from 'lucide-react'
import { Select } from '../components/ui/Select'
import toast from 'react-hot-toast'

interface Project {
  id: string
  name: string
  description: string | null
  target_website: string
  website_category: string | null
  status: string
  run_count: number
  endpoint_count: number
  client_count: number
  last_activity_at: string | null
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

export function ProjectsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const { data, isLoading } = useQuery({
    queryKey: ['projects', { search, status: statusFilter, page }],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      if (search) params.append('search', search)
      if (statusFilter !== 'all') params.append('status', statusFilter)
      const response = await api.get<PaginatedResponse<Project>>(`/projects?${params}`)
      return response.data
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/projects/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Project deleted')
    },
    onError: () => toast.error('Failed to delete project'),
  })

  const archiveMutation = useMutation({
    mutationFn: (id: string) => api.put(`/projects/${id}`, { status: 'archived' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Project archived')
    },
    onError: () => toast.error('Failed to archive project'),
  })

  const handleDelete = (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
      deleteMutation.mutate(id)
    }
  }

  const handleArchive = (id: string, name: string) => {
    if (confirm(`Archive "${name}"? You can restore it later.`)) {
      archiveMutation.mutate(id)
    }
  }

  const projects = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = data?.total_pages ?? 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground mt-1">Manage your API discovery projects</p>
        </div>
        <NavLink to="/projects/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Button>
        </NavLink>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search projects..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full sm:w-48"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Projects Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center py-12">
              <FolderKanban className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium mb-2">No projects found</h3>
              <p className="text-muted-foreground mb-4">
                {search ? 'Try adjusting your search or filters' : 'Get started by creating your first project'}
              </p>
              {!search && (
                <NavLink to="/projects/new">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Project
                  </Button>
                </NavLink>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-4 font-medium text-muted-foreground">Project</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden md:table-cell">Target Website</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden lg:table-cell">Category</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden md:table-cell">Runs</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden lg:table-cell">Endpoints</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden lg:table-cell">Clients</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Status</th>
                    <th className="text-left p-4 font-medium text-muted-foreground hidden md:table-cell">Last Activity</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((project) => (
                    <tr key={project.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                      <td className="p-4">
                        <NavLink to={`/projects/${project.id}`} className="font-medium hover:text-primary transition-colors">
                          {project.name}
                        </NavLink>
                        {project.description && (
                          <p className="text-sm text-muted-foreground truncate max-w-xs mt-1">{project.description}</p>
                        )}
                      </td>
                      <td className="p-4 hidden md:table-cell">
                        <a href={project.target_website} target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1">
                          {project.target_website}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </td>
                      <td className="p-4 hidden lg:table-cell text-sm text-muted-foreground">
                        {project.website_category || '—'}
                      </td>
                      <td className="p-4 hidden md:table-cell text-sm text-muted-foreground">{project.run_count}</td>
                      <td className="p-4 hidden lg:table-cell text-sm text-muted-foreground">{project.endpoint_count}</td>
                      <td className="p-4 hidden lg:table-cell text-sm text-muted-foreground">{project.client_count}</td>
                      <td className="p-4">
                        <Badge
                          variant={
                            project.status === 'active' ? 'success' :
                            project.status === 'archived' ? 'secondary' : 'destructive'
                          }
                        >
                          {project.status}
                        </Badge>
                      </td>
                      <td className="p-4 hidden md:table-cell text-sm text-muted-foreground">
                        {project.last_activity_at ? formatDate(project.last_activity_at) : '—'}
                      </td>
                      <td className="p-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <NavLink to={`/projects/${project.id}`} className="p-2 hover:bg-accent rounded-lg transition-colors" title="View">
                            <ExternalLink className="h-4 w-4" />
                          </NavLink>
                          <Button variant="ghost" size="icon" onClick={() => handleArchive(project.id, project.name)} disabled={project.status === 'archived'} title="Archive">
                            <Archive className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleDelete(project.id, project.name)} title="Delete">
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
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} projects
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}