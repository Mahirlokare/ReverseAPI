import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { formatDate, formatDuration, cn } from '../lib/utils'
import {
  PlayCircle,
  CheckCircle,
  XCircle,
  Clock,
  RotateCcw,
  X,
  ExternalLink,
  Code,
  Database,
  Globe,
  AlertCircle,
  Info,
} from 'lucide-react'
import toast from 'react-hot-toast'

interface Run {
  id: string
  engine_run_id: string | null
  target_url: string
  task: string
  mode: string
  browser_provider: string | null
  ai_provider: string | null
  model: string | null
  output_language: string
  status: string
  exit_code: number | null
  error_summary: string | null
  started_at: string | null
  finished_at: string | null
  duration_seconds: number | null
  execution_config: Record<string, unknown> | null
  project_id: string
  user_id: string
  workspace_id: string
  created_at: string
  updated_at: string
}

interface RunEvent {
  id: string
  run_id: string
  event_type: string
  message: string | null
  metadata: Record<string, unknown> | null
  created_at: string
}

interface RunLog {
  id: string
  run_id: string
  level: string
  message: string
  source: string | null
  created_at: string
}

const statusConfig: Record<string, { label: string; icon: React.ReactNode; variant: 'success' | 'destructive' | 'info' | 'secondary' | 'warning' }> = {
  queued: { label: 'Queued', icon: <Clock className="h-4 w-4" />, variant: 'secondary' },
  initializing: { label: 'Initializing', icon: <LoadingSpinner className="h-4 w-4" />, variant: 'info' },
  browser_starting: { label: 'Browser Starting', icon: <Globe className="h-4 w-4" />, variant: 'info' },
  navigating: { label: 'Navigating', icon: <RotateCcw className="h-4 w-4 animate-spin" />, variant: 'info' },
  interacting: { label: 'Interacting', icon: <PlayCircle className="h-4 w-4" />, variant: 'info' },
  capturing_traffic: { label: 'Capturing Traffic', icon: <Database className="h-4 w-4" />, variant: 'info' },
  analyzing_requests: { label: 'Analyzing Requests', icon: <Code className="h-4 w-4" />, variant: 'info' },
  generating_client: { label: 'Generating Client', icon: <Code className="h-4 w-4" />, variant: 'info' },
  validating_output: { label: 'Validating Output', icon: <CheckCircle className="h-4 w-4" />, variant: 'info' },
  completed: { label: 'Completed', icon: <CheckCircle className="h-4 w-4" />, variant: 'success' },
  failed: { label: 'Failed', icon: <XCircle className="h-4 w-4" />, variant: 'destructive' },
  cancelled: { label: 'Cancelled', icon: <X className="h-4 w-4" />, variant: 'secondary' },
  timed_out: { label: 'Timed Out', icon: <Clock className="h-4 w-4" />, variant: 'destructive' },
}

const activeStatuses = [
  'queued',
  'initializing',
  'browser_starting',
  'navigating',
  'interacting',
  'capturing_traffic',
  'analyzing_requests',
  'generating_client',
  'validating_output',
]

export function RunMonitorPage() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'logs'>('overview')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const { data: run, isLoading, error } = useQuery({
    queryKey: ['runs', runId],
    queryFn: async () => {
      const response = await api.get<Run>(`/runs/${runId}`)
      return response.data
    },
    refetchInterval: (query) => {
      if (!autoRefresh || !query) return false
      const data = query.state?.data as Run | undefined
      if (!data) return 2000
      return activeStatuses.includes(data.status) ? 2000 : false
    },
    enabled: !!runId,
  })

  const { data: events } = useQuery({
    queryKey: ['runs', runId, 'events'],
    queryFn: async () => {
      const response = await api.get<RunEvent[]>(`/runs/${runId}/events`)
      return response.data
    },
    enabled: !!runId && activeTab === 'events',
  })

  const { data: logs } = useQuery({
    queryKey: ['runs', runId, 'logs'],
    queryFn: async () => {
      const response = await api.get<RunLog[]>(`/runs/${runId}/logs?limit=500`)
      return response.data
    },
    enabled: !!runId && activeTab === 'logs',
  })

  const cancelMutation = useMutation({
    mutationFn: () => api.post(`/runs/${runId}/cancel`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs', runId] })
      toast.success('Run cancelled')
    },
    onError: () => toast.error('Failed to cancel run'),
  })

  const retryMutation = useMutation({
    mutationFn: () => api.post(`/runs/${runId}/retry`),
    onSuccess: (response) => {
      toast.success('Run restarted')
      navigate(`/runs/${response.data.id}`)
    },
    onError: () => toast.error('Failed to retry run'),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!run || error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
        <h3 className="text-lg font-medium mb-2">Run not found</h3>
        <p className="text-sm text-muted-foreground mb-4">
          This discovery run could not be found or you do not have permission to view it.
        </p>
        <Button onClick={() => navigate('/projects')} variant="outline">
          Back to Projects
        </Button>
      </div>
    )
  }

  const currentStatus = run.status || 'queued'
  const config = statusConfig[currentStatus] || { label: currentStatus, icon: <Info className="h-4 w-4" />, variant: 'secondary' }
  const isFinished = !activeStatuses.includes(currentStatus)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <Badge variant={config.variant} className="gap-2">
              {config.icon}
              {config.label}
            </Badge>
            {run.engine_run_id && (
              <span className="text-sm text-muted-foreground font-mono">Engine: {run.engine_run_id}</span>
            )}
          </div>
          <h1 className="text-2xl font-bold mt-2">
            {run.task ? (run.task.length > 80 ? run.task.slice(0, 80) + '...' : run.task) : 'API Discovery Run'}
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            {run.target_url} • {formatDate(run.created_at)} • {run.mode || 'agent'} mode
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => setAutoRefresh(!autoRefresh)}>
            {autoRefresh ? 'Pause' : 'Resume'} Auto-refresh
          </Button>
          {!isFinished && (
            <Button
              variant="destructive"
              onClick={() => cancelMutation.mutate()}
              loading={cancelMutation.isPending}
            >
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          )}
          {isFinished && run.status === 'failed' && (
            <Button
              variant="outline"
              onClick={() => retryMutation.mutate()}
              loading={retryMutation.isPending}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          )}
          {isFinished && run.status === 'completed' && run.project_id && (
            <Link to={`/projects/${run.project_id}`}>
              <Button variant="outline">
                <ExternalLink className="h-4 w-4 mr-2" />
                View Project
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {[
          { id: 'overview', label: 'Overview', icon: Info },
          { id: 'events', label: 'Events', icon: Database },
          { id: 'logs', label: 'Logs', icon: Code },
        ].map((tab) => (
          <Button
            key={tab.id}
            variant="ghost"
            className={cn('gap-2', activeTab === tab.id && 'border-b-2 border-primary rounded-none')}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Progress Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Execution Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { key: 'queued', label: 'Queued' },
                  { key: 'initializing', label: 'Initializing' },
                  { key: 'browser_starting', label: 'Browser Starting' },
                  { key: 'navigating', label: 'Navigating' },
                  { key: 'interacting', label: 'Interacting' },
                  { key: 'capturing_traffic', label: 'Capturing Traffic' },
                  { key: 'analyzing_requests', label: 'Analyzing Requests' },
                  { key: 'generating_client', label: 'Generating Client' },
                  { key: 'validating_output', label: 'Validating Output' },
                  { key: 'completed', label: 'Completed' },
                ].map((stage, index) => {
                  const stageOrder = [
                    'queued', 'initializing', 'browser_starting', 'navigating',
                    'interacting', 'capturing_traffic', 'analyzing_requests',
                    'generating_client', 'validating_output', 'completed',
                  ]
                  const currentIdx = stageOrder.indexOf(currentStatus)
                  const thisIdx = stageOrder.indexOf(stage.key)
                  const stageStatus = currentStatus === stage.key
                    ? 'current'
                    : (currentStatus === 'completed' || (currentIdx > thisIdx && currentIdx !== -1))
                    ? 'completed'
                    : 'pending'
                  const isLast = index === 9

                  return (
                    <div key={stage.key} className="flex items-start gap-4">
                      <div className="relative flex flex-col items-center">
                        <div className={cn(
                          'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border-2',
                          stageStatus === 'completed' ? 'bg-primary border-primary text-primary-foreground' :
                          stageStatus === 'current' ? 'bg-primary border-primary text-primary-foreground animate-pulse' :
                          'bg-background border-border text-muted-foreground'
                        )}>
                          {stageStatus === 'completed' && <CheckCircle className="h-5 w-5" />}
                          {stageStatus === 'current' && <LoadingSpinner className="h-5 w-5" />}
                          {stageStatus === 'pending' && (index + 1)}
                        </div>
                        {!isLast && (
                          <div className={cn(
                            'absolute top-8 bottom-0 left-3.5 w-0.5',
                            stageStatus === 'completed' ? 'bg-primary' : 'bg-border'
                          )} />
                        )}
                      </div>
                      <div className="flex-1 pt-1">
                        <p className={cn('font-medium', stageStatus === 'current' ? 'text-foreground' : 'text-muted-foreground')}>
                          {stage.label}
                        </p>
                        {stageStatus === 'current' && (
                          <p className="text-sm text-muted-foreground">In progress...</p>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* Run Details */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-muted-foreground">Run ID</p>
                <p className="font-mono text-sm mt-1 break-all">{run.id}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-muted-foreground">Mode</p>
                <p className="font-medium mt-1 capitalize">{run.mode || 'agent'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-muted-foreground">Output Language</p>
                <p className="font-medium mt-1 capitalize">{run.output_language || 'typescript'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-muted-foreground">{run.duration_seconds ? 'Duration' : 'Elapsed'}</p>
                <p className="font-medium mt-1">
                  {formatDuration(run.duration_seconds)}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Execution Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
                {JSON.stringify(run.execution_config || {}, null, 2)}
              </pre>
            </CardContent>
          </Card>

          {run.error_summary && (
            <Card className="border-destructive/50">
              <CardHeader>
                <CardTitle className="text-destructive flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Error Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-destructive">{run.error_summary}</p>
              </CardContent>
            </Card>
          )}

          {run.status === 'completed' && (
            <Card>
              <CardHeader>
                <CardTitle>Next Steps</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-4">
                {run.project_id && (
                  <Link to={`/projects/${run.project_id}`}>
                    <Button>View Project</Button>
                  </Link>
                )}
                <Link to={`/endpoints?run_id=${run.id}`}>
                  <Button variant="outline">View Endpoints</Button>
                </Link>
                <Link to={`/clients?run_id=${run.id}`}>
                  <Button variant="outline">View Generated Clients</Button>
                </Link>
                <Link to={`/captures?run_id=${run.id}`}>
                  <Button variant="outline">View Captures</Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'events' && (
        <Card>
          <CardContent className="p-0">
            {!events || events.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Database className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                <p>No events recorded yet</p>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {events.map((event) => (
                  <div key={event.id} className="p-4 hover:bg-accent/50 transition-colors">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <Database className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="font-medium capitalize">{event.event_type ? event.event_type.replace(/_/g, ' ') : 'Event'}</p>
                          <p className="text-xs text-muted-foreground">{formatDate(event.created_at)}</p>
                        </div>
                        {event.message && (
                          <p className="text-sm text-muted-foreground mt-1">{event.message}</p>
                        )}
                        {event.metadata && Object.keys(event.metadata).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs text-muted-foreground cursor-pointer">View metadata</summary>
                            <pre className="mt-1 text-xs bg-muted p-2 rounded overflow-x-auto">
                              {JSON.stringify(event.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'logs' && (
        <Card>
          <CardContent className="p-0">
            {!logs || logs.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Code className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                <p>No logs recorded yet</p>
              </div>
            ) : (
              <div className="font-mono text-sm max-h-[500px] overflow-y-auto">
                {logs.slice().reverse().map((log) => (
                  <div
                    key={log.id}
                    className={cn(
                      'px-4 py-1 border-b border-border/50',
                      log.level === 'error' ? 'text-destructive' :
                      log.level === 'warning' ? 'text-amber-500' :
                      log.level === 'debug' ? 'text-muted-foreground' : ''
                    )}
                  >
                    <span className="text-muted-foreground mr-3">{formatDate(log.created_at)}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-muted mr-2">{(log.level || 'info').toUpperCase()}</span>
                    <span className="text-muted-foreground mr-2">[{log.source || 'app'}]</span>
                    <span>{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
