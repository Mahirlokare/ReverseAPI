import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import {
  BookOpen,
  Search,
  FolderKanban,
  PlayCircle,
  Cpu,
  Layers,
  Database,
  Code,
  Shield,
  HelpCircle,
  Terminal,
  FileCode,
  CheckCircle,
  ExternalLink,
} from 'lucide-react'

interface DocSection {
  id: string
  title: string
  category: string
  content: string
}

const docSections: DocSection[] = [
  {
    id: 'getting-started',
    title: '1. Getting Started',
    category: 'Core Concepts',
    content: `Reverse API Engineer is a full-stack platform that transforms web network communication into production-ready API clients without requiring manual browser inspection or terminal commands.

### Key Workflow:
1. **Create Project**: Set up an authorized target workspace.
2. **Configure Discovery**: Provide the URL and objective in natural language.
3. **Execution**: The AI agent navigates the web application, triggering and intercepting real network calls.
4. **Inspection**: Explore endpoints, methods, headers, and request/response payloads.
5. **Code Generation**: Receive idiomatic, typed API client libraries in TypeScript, Python, Go, and more.`,
  },
  {
    id: 'creating-projects',
    title: '2. Creating Projects',
    category: 'Core Concepts',
    content: `Projects group target websites, discovery sessions, captures, endpoints, and generated SDKs.

- **Project Name**: Meaningful identifier (e.g., "Storefront Catalog API").
- **Target Website**: The root URL of the authorized target (e.g., https://example.com/store).
- **Default Language**: Preferred language for generated clients.
- **AI Backend**: Model and provider configuration for the engineering engine.`,
  },
  {
    id: 'api-discovery',
    title: '3. API Discovery Workflow',
    category: 'Discovery & Automation',
    content: `The primary entry point is the guided Discovery form:

1. **Target URL**: Any authorized endpoint or page. All URLs are checked for SSRF protections against internal network targets.
2. **Discovery Task**: Natural language prompt specifying what endpoints or flows to uncover.
   * Example: *"Find the search API used to query inventory with pagination and filters."*
3. **Execution Mode**: Choose between Agent, Manual, or Engineer mode.
4. **Output Language**: Select Python, TypeScript, JavaScript, Go, etc.`,
  },
  {
    id: 'agent-mode',
    title: '4. Agent Mode',
    category: 'Discovery & Automation',
    content: `In Agent mode, the autonomous browsing agent initializes a headless browser, accesses the URL, locates interactive UI components (search bars, filter dropdowns, pagination buttons), and triggers the requisite background network calls while capturing all HTTP transactions.`,
  },
  {
    id: 'manual-capture',
    title: '5. Manual Capture',
    category: 'Discovery & Automation',
    content: `For workflows requiring human interaction or complex multi-step sessions, Manual Mode captures network traffic during interactive sessions. Alternatively, users can import previously exported HAR files directly from browser Developer Tools.`,
  },
  {
    id: 'engineer-mode',
    title: '6. Engineer Mode',
    category: 'Discovery & Automation',
    content: `Engineer mode re-engineers clients from previously saved HAR captures. This enables rapid regeneration of clients in alternative programming languages or with updated models without having to re-run the browser exploration stage.`,
  },
  {
    id: 'browser-providers',
    title: '7. Browser Providers',
    category: 'Execution',
    content: `The engine supports Playwright as the primary headless execution provider. Chrome DevTools Protocol (CDP) / MCP and remote browser bridges are also supported when configured in Settings -> Browser Providers.`,
  },
  {
    id: 'ai-providers',
    title: '8. AI Provider Setup',
    category: 'Execution',
    content: `Multiple AI coding backends are supported:
- **Claude** (Anthropic Claude 3.5 Sonnet / Opus)
- **OpenCode**
- **Cursor**
- **GitHub Copilot**
- **Codex**

Configure API credentials securely under **Settings -> AI Providers**. Keys are encrypted and never exposed to the client.`,
  },
  {
    id: 'endpoint-explorer',
    title: '9. Endpoint Explorer',
    category: 'Inspection & Analysis',
    content: `The Endpoint Explorer lists all observed REST and GraphQL endpoints. Filter by HTTP method (GET, POST, PUT, DELETE), host domain, or search query. Click any endpoint to inspect headers, parameters, and schema models.`,
  },
  {
    id: 'request-response-inspector',
    title: '10. Request & Response Inspector',
    category: 'Inspection & Analysis',
    content: `Inspect exact HTTP wire transactions:
- **Headers**: Complete headers with sensitive tokens automatically masked.
- **Query Params**: Parsed query parameters.
- **Body / Payload**: Syntax-highlighted JSON formatted preview.
- **Response**: HTTP status, response headers, and formatted JSON output.`,
  },
  {
    id: 'har-management',
    title: '11. HAR Capture Management',
    category: 'Inspection & Analysis',
    content: `All network activity is persisted as standardized HTTP Archive (HAR 1.2) files. You can:
- View transaction breakdowns and host distributions.
- Download sanitized or raw HAR files.
- Import external HAR files from browser DevTools to generate new clients.`,
  },
  {
    id: 'generated-api-clients',
    title: '12. Generated API Clients',
    category: 'Generated Artifacts',
    content: `Each client generated is a complete, idiomatic software package including:
- **Client Class**: Type-safe methods for each discovered endpoint.
- **Models**: Data transfer objects with serialization and validation.
- **README.md**: Setup instructions and authentication examples.
- **Example Usage Script**: Ready-to-run script showing real calls.
- **Dependency Manifest**: package.json, requirements.txt, or go.mod.`,
  },
  {
    id: 'client-execution',
    title: '13. Client Execution & Testing',
    category: 'Generated Artifacts',
    content: `Test generated clients directly from the web interface without opening a terminal!
Navigate to **Generated Clients -> Select Client -> Run**, select the entry point (e.g. example_usage.py), and execute in an isolated runtime to verify responses.`,
  },
  {
    id: 'run-history',
    title: '14. Run History & Observability',
    category: 'Monitoring',
    content: `Every execution run maintains full provenance:
- Status transitions timeline.
- Step-by-step event stream.
- Sanitized execution logs.
- Duration and resource metrics.`,
  },
  {
    id: 'storage-downloads',
    title: '15. Storage & Downloads',
    category: 'Generated Artifacts',
    content: `Generated clients can be downloaded as complete ZIP packages or individual files. HAR captures can be exported anytime by authorized project members.`,
  },
  {
    id: 'security-authorized-use',
    title: '16. Security & Authorized Use Policy',
    category: 'Security & Governance',
    content: `**CRITICAL RULES**:
- Only analyze websites, staging environments, and services that you own or have explicit authorization to test.
- The platform enforces automated SSRF protection blocking private RFC-1918 subnets and cloud metadata IPs.
- Sensitive authentication headers and cookies are redacted in persisted captures and UI views.
- No terminal emulators or shell access is ever provided to untrusted users.`,
  },
  {
    id: 'troubleshooting',
    title: '17. Troubleshooting',
    category: 'Support',
    content: `**Common issues & resolutions**:
- **Navigation Timeout**: Ensure the target site is publicly accessible and not blocking headless automation.
- **No Endpoints Discovered**: Verify your discovery prompt describes interactive operations that cause network traffic.
- **Client Execution Error**: Check that target host endpoints are reachable and credentials are valid.`,
  },
  {
    id: 'faq',
    title: '18. Frequently Asked Questions (FAQ)',
    category: 'Support',
    content: `**Q: Do I need to install the CLI on my computer to use the web interface?**
A: No! The web interface communicates with the backend, which manages all execution privately.

**Q: Can I re-generate clients in multiple languages from one run?**
A: Yes! Use Engineer Mode to generate Python, TypeScript, and Go clients from the same captured traffic.

**Q: Where are files stored?**
A: Files are stored privately in your workspace's isolated artifact storage.`,
  },
]

export function DocumentationPage() {
  const [search, setSearch] = useState('')
  const [selectedSectionId, setSelectedSectionId] = useState('getting-started')

  const filteredSections = docSections.filter(
    (s) =>
      s.title.toLowerCase().includes(search.toLowerCase()) ||
      s.content.toLowerCase().includes(search.toLowerCase()) ||
      s.category.toLowerCase().includes(search.toLowerCase())
  )

  const selectedSection =
    docSections.find((s) => s.id === selectedSectionId) || docSections[0]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Documentation & Help Center</h1>
          <p className="text-muted-foreground mt-1">
            Complete platform guide, architectural specifications, and reference manual
          </p>
        </div>
        <Badge variant="outline" className="w-fit">
          Version 1.0
        </Badge>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search documentation topics..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Navigation Sidebar */}
        <div className="space-y-2 lg:col-span-1">
          <Card>
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Topics
              </CardTitle>
            </CardHeader>
            <CardContent className="p-2 space-y-1 max-h-[650px] overflow-y-auto">
              {filteredSections.map((sec) => (
                <button
                  key={sec.id}
                  type="button"
                  onClick={() => setSelectedSectionId(sec.id)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    selectedSectionId === sec.id
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                  }`}
                >
                  {sec.title}
                </button>
              ))}
              {filteredSections.length === 0 && (
                <p className="text-xs text-muted-foreground p-3">No matching topics found.</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Content Viewer */}
        <div className="lg:col-span-3">
          <Card className="min-h-[650px]">
            <CardHeader className="border-b border-border/50">
              <div className="flex items-center justify-between">
                <div>
                  <Badge variant="secondary" className="mb-2">
                    {selectedSection.category}
                  </Badge>
                  <CardTitle className="text-2xl">{selectedSection.title}</CardTitle>
                </div>
                <BookOpen className="h-6 w-6 text-primary/40" />
              </div>
            </CardHeader>
            <CardContent className="p-6 prose prose-invert max-w-none">
              <div className="whitespace-pre-line text-sm leading-relaxed text-foreground/90">
                {selectedSection.content}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
