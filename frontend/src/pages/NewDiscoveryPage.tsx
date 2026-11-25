import { useState } from 'react'
import { useForm, FieldErrors } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Textarea } from '../components/ui/Textarea'
import { Select } from '../components/ui/Select'
import { Label } from '../components/ui/Label'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { cn } from '../lib/utils'
import { ArrowRight, Check, AlertCircle, Info, Globe, Brain, Code, Settings } from 'lucide-react'
import toast from 'react-hot-toast'

// Enums matching backend
const ExecutionMode = {
  AGENT: 'agent',
  MANUAL: 'manual',
  ENGINEER: 'engineer',
} as const

const OutputLanguage = {
  PYTHON: 'python',
  JAVASCRIPT: 'javascript',
  TYPESCRIPT: 'typescript',
  GO: 'go',
  JAVA: 'java',
  CSHARP: 'csharp',
  PHP: 'php',
  RUBY: 'ruby',
  C: 'c',
  POWERSHELL: 'powershell',
} as const

const BrowserProvider = {
  PLAYWRIGHT: 'playwright',
  CHROME_MCP: 'chrome_mcp',
  VERCEL_AGENT_BROWSER: 'vercel_agent_browser',
} as const

const discoverySchema = z.object({
  target_url: z.string().url('Please enter a valid URL (including http:// or https://)'),
  task: z.string().min(10, 'Please describe what you want to discover (at least 10 characters)'),
  project_id: z.string().optional().or(z.literal('')),
  mode: z.nativeEnum(ExecutionMode).default(ExecutionMode.AGENT),
  output_language: z.nativeEnum(OutputLanguage).default(OutputLanguage.TYPESCRIPT),
  ai_provider: z.string().optional(),
  model: z.string().optional(),
  browser_provider: z.nativeEnum(BrowserProvider).default(BrowserProvider.PLAYWRIGHT),
  headless: z.boolean().default(true),
  timeout: z.number().min(60).max(7200).default(3600),
  navigation_instructions: z.string().optional(),
})

type DiscoveryForm = z.infer<typeof discoverySchema>

interface Project {
  id: string
  name: string
  target_website: string
}

interface AIProvider {
  provider: string
  model_id: string
  display_name: string
  is_default: boolean
}

export function NewDiscoveryPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)

  const { data: projects } = useQuery({
    queryKey: ['projects', 'list'],
    queryFn: async () => {
      const response = await api.get<{ items: Project[] }>('/projects?page_size=100&status=active')
      return response.data.items
    },
  })

  const { data: workspaces } = useQuery({
    queryKey: ['workspaces', 'mine'],
    queryFn: async () => {
      const response = await api.get<Array<{ id: string; name: string }>>('/workspaces/me/workspaces')
      return response.data
    },
  })

  const { data: aiProviders } = useQuery({
    queryKey: ['ai-providers'],
    queryFn: async () => {
      const response = await api.get<AIProvider[]>('/ai-providers')
      return response.data
    },
  })

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    trigger,
    formState: { errors, isSubmitting },
  } = useForm<DiscoveryForm>({
    resolver: zodResolver(discoverySchema),
    defaultValues: {
      target_url: '',
      task: '',
      project_id: '',
      mode: ExecutionMode.AGENT,
      output_language: OutputLanguage.TYPESCRIPT,
      browser_provider: BrowserProvider.PLAYWRIGHT,
      headless: true,
      timeout: 3600,
    },
  })

  const watchedMode = watch('mode')
  const watchedOutputLanguage = watch('output_language')

  const createMutation = useMutation({
    mutationFn: (data: DiscoveryForm) => {
      const [provider, selectedModel] = (data.ai_provider || '').split(':', 2)
      const payload: Record<string, unknown> = {
        ...data,
        ai_provider: provider || undefined,
        model: data.model || selectedModel || undefined,
      }
      if (!payload.project_id || (payload.project_id as string).trim() === '') {
        delete payload.project_id
      }
      return api.post('/runs', payload)
    },
    onSuccess: (response) => {
      toast.success('Discovery started!')
      navigate(`/runs/${response.data.id}`)
    },
    onError: (error: unknown) => {
      const axiosError = error as { message?: string; response?: { data?: { detail?: string | Array<{ msg?: string }> } } }
      const detail = axiosError.response?.data?.detail
      const message = Array.isArray(detail) ? detail.map(item => item.msg).filter(Boolean).join('; ') : detail
      toast.error(message || axiosError.message || 'Failed to start discovery')
    },
  })

  const onSubmit = (data: DiscoveryForm) => {
    createMutation.mutate(data)
  }

  const onFormError = (formErrors: FieldErrors<DiscoveryForm>) => {
    const errorKeys = Object.keys(formErrors)
    if (errorKeys.length > 0) {
      const firstKey = errorKeys[0] as keyof DiscoveryForm
      const errorMsg = formErrors[firstKey]?.message || 'Please check form errors'
      toast.error(String(errorMsg))

      if (['target_url', 'task'].includes(firstKey)) {
        setStep(1)
      } else if (['mode', 'output_language', 'browser_provider', 'timeout'].includes(firstKey)) {
        setStep(2)
      }
    }
  }

  const steps = [
    { number: 1, title: 'Target & Task', description: 'Enter the website and what to discover' },
    { number: 2, title: 'Configuration', description: 'Choose execution mode and output settings' },
    { number: 3, title: 'Confirm', description: 'Review and start discovery' },
  ]

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <Label htmlFor="target_url">Target Website URL *</Label>
        <Input
          {...register('target_url')}
          id="target_url"
          placeholder="https://example.com/page"
          error={errors.target_url?.message}
          autoComplete="url"
        />
        <p className="text-sm text-muted-foreground mt-1">
          Enter the full URL of the website you want to analyze. Must include http:// or https://
        </p>
      </div>

      <div>
        <Label htmlFor="task">Discovery Task *</Label>
        <Textarea
          {...register('task')}
          id="task"
          placeholder="Describe what you want to discover. Example: Find the API used to search and retrieve job listings, including pagination and filters."
          error={errors.task?.message}
          rows={4}
        />
        <p className="text-sm text-muted-foreground mt-1">
          Be specific about the functionality you want to investigate. The AI agent will use this to guide its exploration.
        </p>
      </div>

      <div>
        <Label htmlFor="project_id">Project (Optional)</Label>
        <Select
          {...register('project_id')}
          id="project_id"
        >
          <option value="">Create a new project automatically</option>
          {projects?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} — {p.target_website}
            </option>
          ))}
        </Select>
        <p className="text-sm text-muted-foreground mt-1">
          Organize this discovery under an existing project. Leave blank to create a new project automatically.
        </p>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <Label>Execution Mode *</Label>
        <div className="grid gap-3 sm:grid-cols-3 mt-2">
          {[
            { value: ExecutionMode.AGENT, icon: Brain, title: 'Agent Mode', desc: 'AI agent autonomously explores the website' },
            { value: ExecutionMode.MANUAL, icon: Settings, title: 'Manual Mode', desc: 'You interact with the browser while traffic is captured' },
            { value: ExecutionMode.ENGINEER, icon: Code, title: 'Engineer Mode', desc: 'Regenerate client from a previous capture' },
          ].map(({ value, icon: Icon, title, desc }) => (
            <label
              key={value}
              className={cn(
                'relative cursor-pointer',
                watchedMode === value && 'ring-2 ring-primary'
              )}
            >
              <input
                type="radio"
                value={value}
                {...register('mode')}
                className="sr-only"
              />
              <div className={cn(
                'p-4 rounded-lg border transition-all',
                watchedMode === value
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50'
              )}>
                <Icon className="h-6 w-6 text-primary mb-2" />
                <p className="font-medium">{title}</p>
                <p className="text-sm text-muted-foreground mt-1">{desc}</p>
              </div>
            </label>
          ))}
        </div>
        {errors.mode && <p className="text-sm text-destructive mt-1">{errors.mode.message}</p>}
      </div>

      {watchedMode !== ExecutionMode.ENGINEER && (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="output_language">Output Language *</Label>
              <Select
                {...register('output_language')}
                id="output_language"
              >
                {Object.entries(OutputLanguage).map(([key, value]) => (
                  <option key={value} value={value}>{key.charAt(0) + key.slice(1).toLowerCase()}</option>
                ))}
              </Select>
            </div>

            <div>
              <Label htmlFor="browser_provider">Browser Provider</Label>
              <Select
                {...register('browser_provider')}
                id="browser_provider"
                disabled={watchedMode === ExecutionMode.MANUAL}
              >
                {Object.entries(BrowserProvider).map(([key, value]) => (
                  <option key={value} value={value}>{key.replace('_', ' ')}</option>
                ))}
              </Select>
              {watchedMode === ExecutionMode.MANUAL && (
                <p className="text-sm text-muted-foreground mt-1">
                  Manual mode requires a supported browser connection. Currently limited to headless Playwright.
                </p>
              )}
            </div>
          </div>

          <div>
            <Label htmlFor="ai_provider">AI Provider (Optional)</Label>
            <Select
              {...register('ai_provider')}
              id="ai_provider"
            >
              <option value="">Default AI Provider</option>
              {aiProviders?.map((p) => (
                <option key={`${p.provider}-${p.model_id}`} value={`${p.provider}:${p.model_id}`}>
                  {p.display_name || `${p.provider} (${p.model_id})`} {p.is_default && '(default)'}
                </option>
              ))}
            </Select>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="timeout">Timeout (seconds)</Label>
              <Input
                {...register('timeout', { valueAsNumber: true })}
                id="timeout"
                type="number"
                min={60}
                max={7200}
                step={60}
              />
            </div>

            <div>
              <Label htmlFor="headless">Headless Mode</Label>
              <div className="flex items-center space-x-2 mt-1.5">
                <input
                  type="checkbox"
                  {...register('headless')}
                  id="headless"
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <Label htmlFor="headless" className="cursor-pointer mb-0">
                  Run browser in headless mode (no visible UI)
                </Label>
              </div>
            </div>
          </div>
        </>
      )}

      {watchedMode === ExecutionMode.ENGINEER && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">Engineer Mode</p>
              <p className="text-sm text-amber-700 mt-1">
                This mode regenerates a client from a previous capture. You'll need to select a compatible capture
                from your project after submitting. Make sure you have a saved HAR file from a previous run.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  const renderStep3 = () => {
    const formData = watch()
    const taskPreview = formData.task ? (formData.task.length > 80 ? formData.task.slice(0, 80) + '...' : formData.task) : 'None'
    return (
      <div className="space-y-6">
        <div className="p-4 bg-muted/50 rounded-lg">
          <h3 className="font-medium mb-4">Review Configuration</h3>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Target URL</dt>
              <dd className="font-medium truncate max-w-md">{formData.target_url || 'None'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Task</dt>
              <dd className="font-medium truncate max-w-md">{taskPreview}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Execution Mode</dt>
              <dd className="font-medium capitalize">{formData.mode || 'agent'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Output Language</dt>
              <dd className="font-medium capitalize">{formData.output_language || 'typescript'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Browser Provider</dt>
              <dd className="font-medium">{formData.browser_provider || 'playwright'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Headless Mode</dt>
              <dd className="font-medium">{formData.headless ? 'Yes' : 'No'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Timeout</dt>
              <dd className="font-medium">{formData.timeout || 3600}s</dd>
            </div>
            {formData.ai_provider && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">AI Provider</dt>
                <dd className="font-medium">{formData.ai_provider}</dd>
              </div>
            )}
          </dl>
        </div>

        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">Authorization Notice</p>
              <p className="text-sm text-amber-700 mt-1">
                This tool is for authorized testing only. Only use it on websites you own or have explicit permission to test.
                Unauthorized access to private APIs or user accounts is prohibited.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const handleNextStep = async () => {
    if (step === 1) {
      const valid = await trigger(['target_url', 'task'])
      if (!valid) return
    }
    setStep(s => Math.min(3, s + 1))
  }

  const currentStepContent = step === 1 ? renderStep1() : step === 2 ? renderStep2() : renderStep3()

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">New API Discovery</h1>
        <p className="text-muted-foreground mt-1">
          Configure and start a new API discovery session
        </p>
      </div>

      {/* Progress Steps */}
      <div className="hidden md:flex items-center justify-between">
        {steps.map((s, i) => (
          <div key={s.number} className="flex items-center">
            <div className={cn(
              'flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium',
              i + 1 < step ? 'bg-primary text-primary-foreground' :
              i + 1 === step ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
            )}>
              {i + 1 < step ? <Check className="h-4 w-4" /> : s.number}
            </div>
            {i < steps.length - 1 && (
              <div className={cn(
                'w-24 h-1 mx-2',
                i + 1 < step ? 'bg-primary' : 'bg-muted'
              )} />
            )}
            <div className="w-40 text-center">
              <p className={cn(
                'text-sm font-medium',
                i + 1 === step ? 'text-foreground' : 'text-muted-foreground'
              )}>{s.title}</p>
              <p className="text-xs text-muted-foreground">{s.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Mobile step indicator */}
      <div className="md:hidden flex items-center justify-between mb-6">
        {steps.map((s, i) => (
          <div key={s.number} className="flex flex-col items-center">
            <div className={cn(
              'flex items-center justify-center w-10 h-10 rounded-full text-sm font-medium',
              i + 1 < step ? 'bg-primary text-primary-foreground' :
              i + 1 === step ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
            )}>
              {i + 1 < step ? <Check className="h-5 w-5" /> : s.number}
            </div>
            <p className={cn(
              'text-xs mt-1 text-center',
              i + 1 === step ? 'text-foreground' : 'text-muted-foreground'
            )}>{s.title}</p>
          </div>
        ))}
      </div>

      {/* Form */}
      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit(onSubmit, onFormError)} className="space-y-6">
            {currentStepContent}

            {/* Navigation */}
            <div className="flex justify-between pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep(s => Math.max(1, s - 1))}
                disabled={step === 1 || createMutation.isPending}
              >
                <ArrowRight className="h-4 w-4 mr-2 rotate-180" />
                Back
              </Button>
              <div className="flex gap-2">
                {step < 3 && (
                  <Button type="button" onClick={handleNextStep}>
                    Next
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                )}
                {step === 3 && (
                  <Button type="submit" loading={createMutation.isPending || isSubmitting}>
                    Start Discovery
                  </Button>
                )}
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
