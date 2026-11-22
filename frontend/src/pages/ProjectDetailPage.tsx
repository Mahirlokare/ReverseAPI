import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { NavLink } from 'react-router-dom'
import { api } from '../lib/api'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Textarea } from '../components/ui/Textarea'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/Tabs'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { formatDate, cn } from '../lib/utils'
import {
  FolderKanban,
  PlayCircle,
  Globe,
  Code,
  Database,
  Settings,
  Plus,
  ExternalLink,
  Archive,
  Trash2,
  Edit,
} from 'lucide-react'

interface Project {
  id: string
  name: string
  description: string | null
  target_website: string
  website_category: string | null
  default_task: string | null
  default_output_language: string
  default_execution_mode: string
  default_ai_provider: string | null
  default_model: string | null
  status: string
  run_count: number
  endpoint_count: number
  client_count: number
  last_activity_at: string | null
  created_at: string
  updated_at: string
}

interface Run {
  id: string
  target_url: string
  task: string
  mode: string
  status: string
  output_language: string
  started_at: string | null
  finished_at: string | null
  duration_seconds: number | null
  endpoint_count: number
  client_count: number
}

interface Endpoint {
  id: string
  name: string
  method: string
  path: string
  host: string | null
  status_code: number | null
  discovered_at: string
}

interface Capture {
  id: string
  file_path: string
  file_size: number | null
  request_count: number
  target_domain: string | null
  is_sanitized: boolean
  created_at: string
}

interface Client {
  id: string
  name: string
  language: string
  version: string
  file_count: number
  validation_status: string | null
  created_at: string
}

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['projects', projectId],
    queryFn: async () => {
      const response = await api.get<Project>(`/projects/${projectId}`)
      return response.data
    },
    enabled: !!projectId,
  })

  const { data: runs } = useQuery({
    queryKey: ['runs', 'project', projectId],
    queryFn: async () => {
      const response = await api.get<{ items: Run[] }>(`/runs?project_id=${projectId}&page_size=20`)
      return response.data.items
    },
    enabled: !!projectId,
  })

  const { data: endpoints } = useQuery({
    queryKey: ['endpoints', 'project', projectId],
    queryFn: async () => {
      const response = await api.get<{ items: Endpoint[] }>(`/endpoints?project_id=${projectId}&page_size=10`)
      return response.data.items
    },
    enabled: !!projectId,
  })

  const { data: captures } = useQuery({
    queryKey: ['captures', 'project', projectId],
    queryFn: async () => {
      const response = await api.get<{ items: Capture[] }>(`/captures?project_id=${projectId}&page_size=10`)
      return response.data.items
    },
    enabled: !!projectId,
  })

  const { data: clients } = useQuery({
    queryKey: ['clients', 'project', projectId],
    queryFn: async () => {
      const response = await api.get<{ items: Client[] }>(`/clients?project_id=${projectId}&page_size=10`)
      return response.data.items
    },
    enabled: !!projectId,
  })

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <FolderKanban className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
        <h3 className="text-lg font-medium mb-2">Project not found</h3>
        <Button onClick={() => navigate('/projects')} variant="outline">
          Back to Projects
        </Button>
      </div>
    )
  }

  const statusConfig = {
    active: { label: 'Active', variant: 'success' as const },
    archived: { label: 'Archived', variant: 'secondary' as const },
    deleted: { label: 'Deleted', variant: 'destructive' as const },
  }

  const config = statusConfig[project.status as keyof typeof statusConfig] || { label: project.status, variant: 'secondary' as const }

  const projectTabs = [
    { id: 'overview', label: 'Overview', icon: FolderKanban },
    { id: 'runs', label: 'Discovery Runs', icon: PlayCircle, count: project.run_count },
    { id: 'endpoints', label: 'Endpoints', icon: Globe, count: project.endpoint_count },
    { id: 'captures', label: 'Captures', icon: Database, count: captures?.length || 0 },
    { id: 'clients', label: 'Generated Clients', icon: Code, count: project.client_count },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <Badge variant={config.variant} className="gap-2">
              {config.label}
            </Badge>
          </div>
          <h1 className="text-3xl font-bold mt-2">{project.name}</h1>
          <p className="text-muted-foreground mt-1">
            {project.target_website} • Created {formatDate(project.created_at)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <NavLink to={`/projects/${project.id}/runs/new`}>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Discovery
            </Button>
          </NavLink>
          <Button variant="outline" asChild>
            <a href={project.target_website} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-4 w-4 mr-2" />
              View Website
            </a>
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Runs</p>
                <p className="text-3xl font-bold mt-1">{project.run_count}</p>
              </div>
              <div className="p-3 rounded-xl bg-blue-500/10">
                <PlayCircle className="h-6 w-6 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Endpoints</p>
                <p className="text-3xl font-bold mt-1">{project.endpoint_count}</p>
              </div>
              <div className="p-3 rounded-xl bg-green-500/10">
                <Globe className="h-6 w-6 text-green-500" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Clients</p>
                <p className="text-3xl font-bold mt-1">{project.client_count}</p>
              </div>
              <div className="p-3 rounded-xl bg-purple-500/10">
                <Code className="h-6 w-6 text-purple-500" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Captures</p>
                <p className="text-3xl font-bold mt-1">{captures?.length || 0}</p>
              </div>
              <div className="p-3 rounded-xl bg-amber-500/10">
                <Database className="h-6 w-6 text-amber-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-3 md:grid-cols-6">
          {projectTabs.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id} className="gap-2">
              <tab.icon className="h-4 w-4" />
              {tab.label}
              {tab.count !== undefined && (
                <Badge variant="outline" className="ml-auto">{tab.count}</Badge>
              )}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Project Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <dl className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <dt className="text-muted-foreground">Name</dt>
                    <dd className="font-medium">{project.name}</dd>
                    <dt className="text-muted-foreground">Target Website</dt>
                    <dd className="font-medium">
                      <a href={project.target_website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline flex items-center gap-1">
                        {project.target_website}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </dd>
                    <dt className="text-muted-foreground">Category</dt>
                    <dd className="font-medium">{project.website_category || '—'}</dd>
                    <dt className="text-muted-foreground">Status</dt>
                    <dd className="font-medium">
                      <Badge variant={config.variant}>{config.label}</Badge>
                    </dd>
                    <dt className="text-muted-foreground">Default Mode</dt>
                    <dd className="font-medium capitalize">{project.default_execution_mode}</dd>
                    <dt className="text-muted-foreground">Default Language</dt>
                    <dd className="font-medium capitalize">{project.default_output_language}</dd>
                  </div>
                </dl>
                {project.description && (
                  <div>
                    <dt className="text-muted-foreground text-sm">Description</dt>
                    <dd className="mt-1">{project.description}</dd>
                  </div>
                )}
                {project.default_task && (
                  <div>
                    <dt className="text-muted-foreground text-sm">Default Task</dt>
                    <dd className="mt-1 font-mono text-sm bg-muted p-2 rounded">{project.default_task}</dd>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <NavLink to={`/projects/${project.id}/runs/new`}>
                  <Button className="w-full justify-start gap-3">
                    <Plus className="h-4 w-4" />
                    <span>Start New Discovery</span>
                  </Button>
                </NavLink>
                <Button variant="outline" className="w-full justify-start gap-3" onClick={() => navigate(`/projects/${project.id}/settings`)}>
                  <Settings className="h-4 w-4" />
                  <span>Project Settings</span>
                </Button>
                <Button variant="outline" className="w-full justify-start gap-3" onClick={() => navigate(`/endpoints?project_id=${project.id}`)}>
                  <Globe className="h-4 w-4" />
                  <span>View All Endpoints</span>
                </Button>
                <Button variant="outline" className="w-full justify-start gap-3" onClick={() => navigate(`/clients?project_id=${project.id}`)}>
                  <Code className="h-4 w-4" />
                  <span>View All Clients</span>
                </Button>
                <Button variant="outline" className="w-full justify-start gap-3" onClick={() => navigate(`/captures?project_id=${project.id}`)}>
                  <Database className="h-4 w-4" />
                  <span>View All Captures</span>
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="runs" className="space-y-4">
          {runs?.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <PlayCircle className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-medium mb-2">No runs yet</h3>
                <NavLink to={`/projects/${project.id}/runs/new`}>
                  <Button>Start First Discovery</Button>
                </NavLink>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-4 font-medium text-muted-foreground">Task</th>
                        <th className="text-left p-4 font-medium text-muted-foreground hidden md:table-cell">Target URL</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Mode</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Status</th>
                        <th className="text-left p-4 font-medium text-muted-foreground hidden md:table-cell">Duration</th>
                        <th className="text-left p-4 font-medium text-muted-foreground hidden lg:table-cell">Endpoints</th>
                        <th className="text-left p-4 font-medium text-muted-foreground hidden lg:table-cell">Clients</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Started</th>
                      </tr>
                    </thead>
                    <tbody>
                      {runs?.map((run) => (
                        <tr key={run.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors cursor-pointer"
                          onClick={() => navigate(`/runs/${run.id}`)}>
                        <td className="p-4 font-medium">{run.task.slice(0, 60)}</td>
                        <td className="p-4 hidden md:table-cell text-sm text-muted-foreground truncate max-w-xs">{run.target_url}</td>
                        <td className="p-4">
                          <Badge variant="outline">{run.mode}</Badge>
                        </td>
                        <td className="p-4">
                          <Badge
                            variant={
                              run.status === 'completed' ? 'success' :
                              run.status === 'failed' ? 'destructive' :
                              run.status === 'running' || run.status === 'queued' ? 'info' :
                              'secondary'
                            }
                          >
                            {run.status}
                          </Badge>
                        </td>
                        <td className="p-4 hidden md:table-cell text-sm text-muted-foreground">
                          {run.duration_seconds ? formatDate(run.finished_at || '') : 'Running...'}
                        </td>
                        <td className="p-4 hidden lg:table-cell text-sm text-muted-foreground">{run.endpoint_count}</td>
                        <td className="p-4 hidden lg:table-cell text-sm text-muted-foreground">{run.client_count}</td>
                        <td className="p-4 text-sm text-muted-foreground">{formatDate(run.started_at || '')}</td>
                      </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="endpoints" className="space-y-4">
          {endpoints?.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <Globe className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-medium mb-2">No endpoints discovered</h3>
                <p className="text-muted-foreground mb-4">Run a discovery to find API endpoints</p>
                <NavLink to={`/projects/${project.id}/runs/new`}>
                  <Button>Start Discovery</Button>
                </NavLink>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-4 font-medium text-muted-foreground">Endpoint</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Method</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Path</th>
                        <th className="text-left p-4 font-medium text-muted-foreground hidden md:table-cell">Host</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Status</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Discovered</th>
                      </tr>
                    </thead>
                    <tbody>
                      {endpoints?.map((ep) => (
                        <tr key={ep.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                          <td className="p-4 font-medium">{ep.name}</td>
                          <td className="p-4">
                            <Badge variant="outline">{ep.method}</Badge>
                          </td>
                          <td className="p-4 font-mono text-sm">{ep.path}</td>
                          <td className="p-4 hidden md:table-cell text-sm text-muted-foreground">{ep.host || '—'}</td>
                          <td className="p-4">
                            {ep.status_code ? (
                              <Badge variant={ep.status_code >= 200 && ep.status_code < 300 ? 'success' : 'destructive'}>
                                {ep.status_code}
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </td>
                          <td className="p-4 text-sm text-muted-foreground">{formatDate(ep.discovered_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="captures" className="space-y-4">
          {captures?.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <Database className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-medium mb-2">No captures</h3>
                <p className="text-muted-foreground mb-4">Run a discovery to capture network traffic</p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-4 font-medium text-muted-foreground">Capture</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Domain</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Requests</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Size</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Sanitized</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {captures?.map((cap) => (
                        <tr key={cap.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                          <td className="p-4 font-medium">{cap.file_path.split('/').pop()}</td>
                          <td className="p-4 text-sm text-muted-foreground">{cap.target_domain || '—'}</td>
                          <td className="p-4 text-sm text-muted-foreground">{cap.request_count}</td>
                          <td className="p-4 text-sm text-muted-foreground">{cap.file_size ? (cap.file_size / 1024).toFixed(1) + ' KB' : '—'}</td>
                          <td className="p-4">
                            <Badge variant={cap.is_sanitized ? 'success' : 'outline'}>
                              {cap.is_sanitized ? 'Yes' : 'No'}
                            </Badge>
                          </td>
                          <td className="p-4 text-sm text-muted-foreground">{formatDate(cap.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="clients" className="space-y-4">
          {clients?.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <Code className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-medium mb-2">No clients generated</h3>
                <p className="text-muted-foreground mb-4">Run a discovery to generate API clients</p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-4 font-medium text-muted-foreground">Client</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Language</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Version</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Files</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Validation</th>
                        <th className="text-left p-4 font-medium text-muted-foreground">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {clients?.map((client) => (
                        <tr key={client.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                          <td className="p-4 font-medium">{client.name}</td>
                          <td className="p-4">
                            <Badge variant="outline">{client.language}</Badge>
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
                          <td className="p-4 text-sm text-muted-foreground">{formatDate(client.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Project Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium mb-1">Project Name</label>
                    <Input defaultValue={project.name} disabled />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Target Website</label>
                    <Input defaultValue={project.target_website} disabled />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Description</label>
                  <Textarea defaultValue={project.description || ''} disabled rows={3} />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium mb-1">Default Execution Mode</label>
                    <Select defaultValue={project.default_execution_mode} disabled>
                      <option value="agent">Agent</option>
                      <option value="manual">Manual</option>
                      <option value="engineer">Engineer</option>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Default Output Language</label>
                    <Select defaultValue={project.default_output_language} disabled>
                      <option value="typescript">TypeScript</option>
                      <option value="python">Python</option>
                      <option value="javascript">JavaScript</option>
                    </Select>
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button variant="outline">Save Changes</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}