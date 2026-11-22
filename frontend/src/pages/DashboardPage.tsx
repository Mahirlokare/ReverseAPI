import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { formatDuration, cn } from '../lib/utils'
import {
  FolderKanban,
  PlayCircle,
  CheckCircle,
  XCircle,
  Clock,
  Globe,
  Code,
  Database,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'

interface Project {
  id: string
  name: string
  target_website: string
  status: string
  run_count: number
  endpoint_count: number
  client_count: number
  last_activity_at: string | null
  created_at: string
}

interface Run {
  id: string
  project_id: string
  target_url: string
  task: string
  status: string
  mode: string
  created_at: string
  finished_at: string | null
  duration_seconds: number | null
}

interface Stats {
  total_projects: number
  total_runs: number
  successful_runs: number
  failed_runs: number
  running_jobs: number
  total_endpoints: number
  total_clients: number
  total_captures: number
}

export function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await api.get<Stats>('/health/stats') // This endpoint would need to be created
      return response.data
    },
  })

  const { data: recentProjects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects', 'recent'],
    queryFn: async () => {
      const response = await api.get<{ items: Project[] }>('/projects?page_size=5')
      return response.data.items
    },
  })

  const { data: recentRuns, isLoading: runsLoading } = useQuery({
    queryKey: ['runs', 'recent'],
    queryFn: async () => {
      const response = await api.get<{ items: Run[] }>('/runs?page_size=10')
      return response.data.items
    },
  })

  const statCards = [
    {
      name: 'Total Projects',
      value: stats?.total_projects ?? 0,
      icon: FolderKanban,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      trend: '+12%',
      trendIcon: ArrowUpRight,
    },
    {
      name: 'Discovery Runs',
      value: stats?.total_runs ?? 0,
      icon: PlayCircle,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      trend: '+8%',
      trendIcon: ArrowUpRight,
    },
    {
      name: 'Success Rate',
      value: stats?.total_runs ? Math.round((stats.successful_runs / stats.total_runs) * 100) + '%' : '0%',
      icon: CheckCircle,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-500/10',
      trend: '+2%',
      trendIcon: ArrowUpRight,
    },
    {
      name: 'Running Jobs',
      value: stats?.running_jobs ?? 0,
      icon: Clock,
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/10',
      trend: stats?.running_jobs ? 'Active' : 'Idle',
      trendIcon: ArrowDownRight,
    },
  ]

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Overview of your API engineering activity
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.name}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{stat.name}</p>
                  <p className="text-3xl font-bold mt-1">{stat.value}</p>
                  <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                    <stat.trendIcon className="h-3 w-3" />
                    <span>{stat.trend}</span>
                  </p>
                </div>
                <div className={cn('p-3 rounded-xl', stat.bgColor)}>
                  <stat.icon className={cn('h-6 w-6', stat.color)} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Recent Projects */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Projects</CardTitle>
          </CardHeader>
          <CardContent>
            {projectsLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : recentProjects?.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FolderKanban className="mx-auto h-12 w-12 text-muted-foreground/50 mb-2" />
                <p>No projects yet</p>
                <a href="/projects/new" className="text-primary hover:underline mt-2 inline-block">
                  Create your first project
                </a>
              </div>
            ) : (
              <div className="space-y-3">
                {recentProjects?.map((project: Project) => (
                  <div
                    key={project.id}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors cursor-pointer"
                    onClick={() => window.location.href = `/projects/${project.id}`}
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <FolderKanban className="h-5 w-5 text-primary" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium truncate">{project.name}</p>
                        <p className="text-sm text-muted-foreground truncate">{project.target_website}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={project.status === 'active' ? 'success' : 'secondary'}>
                        {project.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {project.run_count} runs
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Runs */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Runs</CardTitle>
          </CardHeader>
          <CardContent>
            {runsLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : recentRuns?.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <PlayCircle className="mx-auto h-12 w-12 text-muted-foreground/50 mb-2" />
                <p>No runs yet</p>
                <a href="/projects/new" className="text-primary hover:underline mt-2 inline-block">
                  Start a discovery
                </a>
              </div>
            ) : (
              <div className="space-y-3">
                {recentRuns?.map((run: Run) => (
                  <div
                    key={run.id}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors cursor-pointer"
                    onClick={() => window.location.href = `/runs/${run.id}`}
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <div className={cn(
                        'h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0',
                        run.status === 'completed' ? 'bg-green-500/10' :
                        run.status === 'failed' ? 'bg-red-500/10' :
                        run.status === 'running' || run.status === 'queued' ? 'bg-blue-500/10' :
                        'bg-gray-500/10'
                      )}>
                        {run.status === 'completed' && <CheckCircle className="h-5 w-5 text-green-500" />}
                        {run.status === 'failed' && <XCircle className="h-5 w-5 text-red-500" />}
                        {run.status === 'running' && <LoadingSpinner className="h-5 w-5 text-blue-500" />}
                        {run.status === 'queued' && <Clock className="h-5 w-5 text-blue-500" />}
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium truncate">{run.task.slice(0, 50)}...</p>
                        <p className="text-sm text-muted-foreground truncate">{run.target_url}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 text-right">
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
                      {run.duration_seconds && (
                        <span className="text-xs text-muted-foreground">
                          {formatDuration(run.duration_seconds)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Endpoints Discovered</p>
                <p className="text-3xl font-bold mt-1">{stats?.total_endpoints ?? 0}</p>
              </div>
              <div className="p-3 rounded-xl bg-purple-500/10">
                <Globe className="h-6 w-6 text-purple-500" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Generated Clients</p>
                <p className="text-3xl font-bold mt-1">{stats?.total_clients ?? 0}</p>
              </div>
              <div className="p-3 rounded-xl bg-indigo-500/10">
                <Code className="h-6 w-6 text-indigo-500" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Captures Stored</p>
                <p className="text-3xl font-bold mt-1">{stats?.total_captures ?? 0}</p>
              </div>
              <div className="p-3 rounded-xl bg-amber-500/10">
                <Database className="h-6 w-6 text-amber-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}