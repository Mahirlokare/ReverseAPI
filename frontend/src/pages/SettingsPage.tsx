import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Label } from '../components/ui/Label'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/Tabs'
import { Badge } from '../components/ui/Badge'
import { Switch } from '../components/ui/Switch'
import { cn } from '../lib/utils'
import { User, Shield, Globe, Settings, Bell, Palette, Moon, Sun, Monitor, Trash2, Brain } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '../lib/auth'

interface UserProfile {
  id: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
}

interface AIProviderConfig {
  id: string
  provider: string
  model_id: string
  display_name: string
  auth_status: string
  provider_settings: Record<string, unknown>
  is_default: boolean
  is_enabled: boolean
  last_health_check: string | null
  health_check_status: string | null
}

interface BrowserProviderConfig {
  id: string
  provider: string
  is_available: boolean
  health_status: string | null
  config: Record<string, unknown>
}

interface UserPreferences {
  theme: string
  language: string
  timezone: string
  notifications_enabled: boolean
  email_notifications: boolean
  compact_mode: boolean
  sidebar_collapsed: boolean
}

export function SettingsPage() {
  const { user, setUser } = useAuthStore()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('general')

  const { data: profile } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const response = await api.get<UserProfile>('/auth/me')
      return response.data
    },
  })

  const { data: aiProviders } = useQuery({
    queryKey: ['ai-providers'],
    queryFn: async () => {
      const response = await api.get<AIProviderConfig[]>('/ai-providers')
      return response.data
    },
  })

  const { data: browserProviders } = useQuery({
    queryKey: ['browser-providers'],
    queryFn: async () => {
      const response = await api.get<BrowserProviderConfig[]>('/browser-providers')
      return response.data
    },
  })

  const { data: preferences } = useQuery({
    queryKey: ['user', 'preferences'],
    queryFn: async () => {
      const response = await api.get<UserPreferences>('/settings/preferences')
      return response.data
    },
  })

  const updateProfileMutation = useMutation({
    mutationFn: (data: Partial<UserProfile>) => api.put('/auth/me', data),
    onSuccess: (res: any) => {
      setUser(res.data)
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
      toast.success('Profile updated')
    },
    onError: () => toast.error('Failed to update profile'),
  })

  const updatePreferencesMutation = useMutation({
    mutationFn: (data: Partial<UserPreferences>) => api.put('/settings/preferences', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] })
      toast.success('Preferences saved')
    },
    onError: () => toast.error('Failed to save preferences'),
  })

  const _addProviderMutation = useMutation({
    mutationFn: (data: { provider: string; model_id: string; display_name?: string; provider_settings?: Record<string, unknown> }) =>
      api.post('/ai-providers', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-providers'] })
      toast.success('Provider added')
    },
    onError: () => toast.error('Failed to add provider'),
  })

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'ai-providers', label: 'AI Providers', icon: Brain },
    { id: 'browser', label: 'Browser', icon: Globe },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your account and application preferences</p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 md:grid-cols-7">
          {tabs.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id} className="gap-2">
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {/* General */}
        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Application</CardTitle>
              <CardDescription>General application settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="app_name">Application Name</Label>
                  <Input id="app_name" defaultValue="Reverse API Engineer" disabled />
                </div>
                <div>
                  <Label htmlFor="workspace_name">Workspace Name</Label>
                  <Input id="workspace_name" defaultValue={user?.email?.split('@')[0] || 'My Workspace'} />
                </div>
              </div>
              <div>
                <Label htmlFor="default_mode">Default Discovery Mode</Label>
                <Select id="default_mode" defaultValue="agent">
                  <option value="agent">Agent Mode</option>
                  <option value="manual">Manual Mode</option>
                  <option value="engineer">Engineer Mode</option>
                </Select>
              </div>
              <div>
                <Label htmlFor="default_language">Default Output Language</Label>
                <Select id="default_language" defaultValue="typescript">
                  <option value="typescript">TypeScript</option>
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="go">Go</option>
                  <option value="java">Java</option>
                </Select>
              </div>
              <div>
                <Label htmlFor="default_timeout">Default Execution Timeout (seconds)</Label>
                <Input id="default_timeout" type="number" defaultValue="3600" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Profile */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>Update your personal information</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={(e) => {
                e.preventDefault()
                const formData = new FormData(e.currentTarget)
                updateProfileMutation.mutate({
                  full_name: formData.get('full_name') as string,
                  email: formData.get('email') as string,
                })
              }} className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input id="full_name" name="full_name" defaultValue={profile?.full_name || ''} />
                  </div>
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" name="email" type="email" defaultValue={profile?.email || ''} />
                  </div>
                </div>
                <div>
                  <Label htmlFor="password">New Password (leave blank to keep current)</Label>
                  <Input id="password" name="password" type="password" placeholder="••••••••" />
                </div>
                <div>
                  <Label htmlFor="confirm_password">Confirm New Password</Label>
                  <Input id="confirm_password" name="confirm_password" type="password" placeholder="••••••••" />
                </div>
                <Button type="submit">Save Changes</Button>
              </form>
            </CardContent>
          </Card>

          <Card className="border-destructive/50">
            <CardHeader>
              <CardTitle className="text-destructive flex items-center gap-2">
                <Trash2 className="h-5 w-5" />
                Danger Zone
              </CardTitle>
              <CardDescription>Irreversible actions</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="destructive" onClick={() => {}}>Delete Account</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Providers */}
        <TabsContent value="ai-providers" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>AI Provider Configurations</CardTitle>
                <CardDescription>Configure AI providers for client generation</CardDescription>
              </div>
              <Button onClick={() => {}}>Add Provider</Button>
            </CardHeader>
            <CardContent>
              {aiProviders?.length === 0 ? (
                <div className="text-center py-8">
                  <Brain className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-medium mb-2">No AI providers configured</h3>
                  <p className="text-muted-foreground mb-4">Add an AI provider to enable client generation</p>
                  <Button onClick={() => {}}>Add Provider</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {aiProviders?.map((provider: AIProviderConfig) => (
                    <div key={provider.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Brain className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{provider.display_name || `${provider.provider} (${provider.model_id})`}</p>
                          <p className="text-sm text-muted-foreground">{provider.provider} • {provider.model_id}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <Badge variant={provider.auth_status === 'validated' ? 'success' : 'secondary'}>
                          {provider.auth_status}
                        </Badge>
                        <Badge variant={provider.is_default ? 'default' : 'outline'}>
                          {provider.is_default ? 'Default' : 'Available'}
                        </Badge>
                        {provider.is_enabled ? (
                          <Badge variant="success">Enabled</Badge>
                        ) : (
                          <Badge variant="secondary">Disabled</Badge>
                        )}
                        <Button variant="ghost" size="icon">Edit</Button>
                        <Button variant="ghost" size="icon" onClick={() => {}}>Test</Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Browser */}
        <TabsContent value="browser" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Browser Providers</CardTitle>
              <CardDescription>Configure browser automation providers</CardDescription>
            </CardHeader>
            <CardContent>
              {browserProviders?.length === 0 ? (
                <div className="text-center py-8">
                  <Globe className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-medium mb-2">No browser providers configured</h3>
                  <p className="text-muted-foreground">Playwright is used by default</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {browserProviders?.map((provider: BrowserProviderConfig) => (
                    <div key={provider.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                          <Globe className="h-5 w-5 text-green-500" />
                        </div>
                        <div>
                          <p className="font-medium capitalize">{provider.provider.replace('_', ' ')}</p>
                          <p className="text-sm text-muted-foreground">Browser automation provider</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <Badge variant={provider.is_available ? 'success' : 'destructive'}>
                          {provider.is_available ? 'Available' : 'Unavailable'}
                        </Badge>
                        <Badge variant="outline">{provider.health_status || 'Unknown'}</Badge>
                        <Button variant="ghost" size="icon">Configure</Button>
                        <Button variant="ghost" size="icon" onClick={() => {}}>Test</Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Execution Settings</CardTitle>
              <CardDescription>Configure default execution parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="max_concurrent">Max Concurrent Jobs</Label>
                  <Input id="max_concurrent" type="number" defaultValue="3" min="1" max="10" />
                </div>
                <div>
                  <Label htmlFor="max_duration">Max Execution Duration (seconds)</Label>
                  <Input id="max_duration" type="number" defaultValue="3600" min="60" max="7200" />
                </div>
              </div>
              <div>
                <Label htmlFor="artifact_retention">Artifact Retention (days)</Label>
                <Input id="artifact_retention" type="number" defaultValue="30" min="1" max="365" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance */}
        <TabsContent value="appearance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Theme</CardTitle>
              <CardDescription>Choose your preferred color theme</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                {['light', 'dark', 'system'].map((theme) => (
                  <label key={theme} className={cn(
                    'flex-1 p-4 rounded-lg border-2 transition-all cursor-pointer',
                    preferences?.theme === theme
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  )}>
                    <input
                      type="radio"
                      name="theme"
                      value={theme}
                      defaultChecked={preferences?.theme === theme}
                      onChange={() => updatePreferencesMutation.mutate({ theme })}
                      className="sr-only"
                    />
                    <div className="flex flex-col items-center gap-2">
                      {theme === 'light' && <Sun className="h-8 w-8" />}
                      {theme === 'dark' && <Moon className="h-8 w-8" />}
                      {theme === 'system' && <Monitor className="h-8 w-8" />}
                      <span className="font-medium capitalize">{theme}</span>
                    </div>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Interface</CardTitle>
              <CardDescription>Customize the interface</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Compact Mode</p>
                  <p className="text-sm text-muted-foreground">Reduce spacing for denser layout</p>
                </div>
                <Switch
                  checked={preferences?.compact_mode || false}
                  onCheckedChange={(checked) => updatePreferencesMutation.mutate({ compact_mode: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Sidebar Collapsed</p>
                  <p className="text-sm text-muted-foreground">Keep sidebar collapsed by default</p>
                </div>
                <Switch
                  checked={preferences?.sidebar_collapsed || false}
                  onCheckedChange={(checked) => updatePreferencesMutation.mutate({ sidebar_collapsed: checked })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>Configure how you receive notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">In-App Notifications</p>
                  <p className="text-sm text-muted-foreground">Receive notifications in the app</p>
                </div>
                <Switch
                  checked={preferences?.notifications_enabled ?? true}
                  onCheckedChange={(checked) => updatePreferencesMutation.mutate({ notifications_enabled: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Email Notifications</p>
                  <p className="text-sm text-muted-foreground">Receive email notifications for important events</p>
                </div>
                <Switch
                  checked={preferences?.email_notifications ?? false}
                  onCheckedChange={(checked) => updatePreferencesMutation.mutate({ email_notifications: checked })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
              <CardDescription>Manage your account security</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label htmlFor="current_password">Current Password</Label>
                <Input id="current_password" type="password" placeholder="••••••••" />
              </div>
              <div>
                <Label htmlFor="new_password">New Password</Label>
                <Input id="new_password" type="password" placeholder="••••••••" />
              </div>
              <div>
                <Label htmlFor="confirm_new_password">Confirm New Password</Label>
                <Input id="confirm_new_password" type="password" placeholder="••••••••" />
              </div>
              <Button>Update Password</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>Manage your API keys for programmatic access</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" onClick={() => {}}>Generate API Key</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}