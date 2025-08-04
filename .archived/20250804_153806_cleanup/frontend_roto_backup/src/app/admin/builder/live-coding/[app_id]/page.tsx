"use client"

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import dynamic from 'next/dynamic'
import { ApiClient } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  FolderIcon, 
  FileIcon, 
  CodeIcon, 
  EyeIcon, 
  EyeOffIcon, 
  PanelLeftIcon, 
  SaveIcon, 
  RefreshCwIcon,
  MessageSquareIcon,
  SendIcon,
  BotIcon,
  UserIcon,
  ChevronRightIcon,
  ChevronDownIcon
} from 'lucide-react'

// Importar Monaco Editor de manera dinámica para evitar SSR
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center h-full">Cargando editor...</div>
})

interface FileNode {
  path: string
  size: number
  modified: string
  isDirectory?: boolean
  children?: FileNode[]
  isExpanded?: boolean
}

interface AppData {
  app_id: string
  app_name: string
  status: string
  endpoints: {
    frontend?: string
    api?: string
    admin?: string
    local_path?: string
  }
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  agent?: string
  timestamp: number
}

export default function LiveCodingPage() {
  const params = useParams()
  const app_id = params.app_id as string
  
  const [appData, setAppData] = useState<AppData | null>(null)
  const [files, setFiles] = useState<FileNode[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string>('')
  
  // Layout state
  const [showCodePanel, setShowCodePanel] = useState(false)
  const [showFileExplorer, setShowFileExplorer] = useState(false)
  
  // AI Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState('code-assistant')

  // Available AI agents
  const agents = [
    { id: 'code-assistant', name: 'Code Assistant', icon: CodeIcon, color: 'text-blue-600' },
    { id: 'ui-designer', name: 'UI Designer', icon: EyeIcon, color: 'text-purple-600' },
    { id: 'performance-optimizer', name: 'Performance', icon: RefreshCwIcon, color: 'text-green-600' },
    { id: 'security-auditor', name: 'Security', icon: BotIcon, color: 'text-red-600' },
  ]

  // Cargar datos de la aplicación
  useEffect(() => {
    const loadAppData = async () => {
      try {
        const response = await ApiClient.get(`/api/builder/projects/${app_id}`)
        if (response.ok) {
          const data = await response.json()
          setAppData(data)
          setPreviewUrl(data.endpoints?.frontend || '')
        }
      } catch (error) {
        console.error('Error loading app data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    if (app_id) {
      loadAppData()
    }
  }, [app_id])

  // Cargar archivos del proyecto
  useEffect(() => {
    const loadFiles = async () => {
      try {
        const response = await ApiClient.get(`/v1/apps/${app_id}/files`)
        if (response.ok) {
          const data = await response.json()
          const tree = buildFileTree(data.files || [])
          setFiles(tree)
        }
      } catch (error) {
        console.error('Error loading files:', error)
      }
    }

    if (app_id) {
      loadFiles()
    }
  }, [app_id])

  // Construir árbol de archivos
  const buildFileTree = (files: FileNode[]): FileNode[] => {
    const tree: FileNode[] = []
    const pathMap = new Map<string, FileNode>()

    // Filtrar archivos relevantes
    const relevantFiles = files.filter(file => 
      !file.path.includes('node_modules') && 
      !file.path.includes('.next') &&
      !file.path.includes('.git') &&
      !file.path.includes('__pycache__') &&
      (file.path.endsWith('.tsx') || 
       file.path.endsWith('.ts') || 
       file.path.endsWith('.js') || 
       file.path.endsWith('.jsx') || 
       file.path.endsWith('.py') ||
       file.path.endsWith('.json') ||
       file.path.endsWith('.md'))
    )

    relevantFiles.forEach(file => {
      const parts = file.path.split('/')
      let currentPath = ''
      
      parts.forEach((part, index) => {
        const previousPath = currentPath
        currentPath = currentPath ? `${currentPath}/${part}` : part
        
        if (!pathMap.has(currentPath)) {
          const node: FileNode = {
            path: currentPath,
            size: file.size,
            modified: file.modified,
            isDirectory: index < parts.length - 1,
            children: [],
            isExpanded: false
          }
          pathMap.set(currentPath, node)
          
          if (previousPath) {
            const parent = pathMap.get(previousPath)
            if (parent) {
              parent.children!.push(node)
            }
          } else {
            tree.push(node)
          }
        }
      })
    })

    return tree
  }

  // Cargar contenido de archivo
  const loadFileContent = async (filePath: string) => {
    try {
      const response = await ApiClient.get(`/v1/apps/${app_id}/file/${filePath}`)
      if (response.ok) {
        const data = await response.json()
        setFileContent(data.content || '')
        setSelectedFile(filePath)
        setShowCodePanel(true) // Mostrar panel de código automáticamente
      }
    } catch (error) {
      console.error('Error loading file content:', error)
    }
  }

  // Guardar contenido de archivo
  const saveFileContent = async (content?: string) => {
    if (!selectedFile) return
    
    const contentToSave = content || fileContent
    setIsSaving(true)
    
    try {
      const response = await ApiClient.put(`/v1/apps/${app_id}/file/${selectedFile}`, {
        content: contentToSave
      })
      if (response.ok) {
        setFileContent(contentToSave)
        // Recargar preview
        if (previewUrl) {
          const iframe = document.getElementById('preview-iframe') as HTMLIFrameElement
          if (iframe) {
            iframe.src = iframe.src
          }
        }
      }
    } catch (error) {
      console.error('Error saving file:', error)
    } finally {
      setIsSaving(false)
    }
  }

  // Enviar mensaje al chat de IA
  const sendChatMessage = async () => {
    if (!chatInput.trim()) return
    
    const userMessage: ChatMessage = {
      role: 'user',
      content: chatInput,
      timestamp: Date.now()
    }
    
    setChatMessages(prev => [...prev, userMessage])
    setChatInput('')
    setIsGenerating(true)

    try {
      const response = await ApiClient.post(`/v1/apps/${app_id}/ai/generate`, {
        prompt: chatInput,
        agent: selectedAgent,
        file_path: selectedFile,
        current_content: fileContent,
        context: 'live-coding'
      })
      
      if (response.ok) {
        const data = await response.json()
        const aiMessage: ChatMessage = {
          role: 'assistant',
          content: data.response || 'No se pudo generar una respuesta',
          agent: selectedAgent,
          timestamp: Date.now()
        }
        setChatMessages(prev => [...prev, aiMessage])
        
        // Si hay código generado, actualizarlo
        if (data.generated_code && selectedFile) {
          setFileContent(data.generated_code)
        }
      }
    } catch (error) {
      console.error('Error generating code:', error)
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: No se pudo conectar con el agente IA',
        agent: selectedAgent,
        timestamp: Date.now()
      }])
    } finally {
      setIsGenerating(false)
    }
  }

  // Toggle directory expansion
  const toggleDirectory = (path: string) => {
    const toggleNode = (nodes: FileNode[]): FileNode[] => {
      return nodes.map(node => {
        if (node.path === path && node.isDirectory) {
          return { ...node, isExpanded: !node.isExpanded }
        }
        if (node.children) {
          return { ...node, children: toggleNode(node.children) }
        }
        return node
      })
    }
    
    setFiles(toggleNode(files))
  }

  // Renderizar árbol de archivos
  const renderFileTree = (nodes: FileNode[], level = 0) => {
    return nodes.map(node => {
      const isExpandable = node.isDirectory && node.children && node.children.length > 0
      const isExpanded = node.isExpanded
      
      return (
        <div key={node.path}>
          <div
            className={`flex items-center gap-2 p-1 hover:bg-gray-100 cursor-pointer text-sm ${
              selectedFile === node.path ? 'bg-blue-100 text-blue-700' : 'text-gray-700'
            }`}
            style={{ paddingLeft: `${level * 12 + 8}px` }}
            onClick={() => {
              if (node.isDirectory) {
                toggleDirectory(node.path)
              } else {
                loadFileContent(node.path)
              }
            }}
          >
            {isExpandable && (
              isExpanded ? 
                <ChevronDownIcon className="w-3 h-3" /> : 
                <ChevronRightIcon className="w-3 h-3" />
            )}
            {!isExpandable && node.isDirectory && <div className="w-3 h-3" />}
            
            {node.isDirectory ? (
              <FolderIcon className="w-3 h-3 text-blue-500" />
            ) : (
              <FileIcon className="w-3 h-3 text-gray-500" />
            )}
            
            <span className="text-xs truncate">{node.path.split('/').pop()}</span>
          </div>
          
          {isExpandable && isExpanded && node.children && (
            <div>
              {renderFileTree(node.children, level + 1)}
            </div>
          )}
        </div>
      )
    })
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault()
        saveFileContent()
      }
      if (e.ctrlKey && e.key === 'j') {
        e.preventDefault()
        setShowCodePanel(!showCodePanel)
      }
      if (e.ctrlKey && e.key === 'e') {
        e.preventDefault()
        setShowFileExplorer(!showFileExplorer)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [showCodePanel, showFileExplorer])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCwIcon className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>Cargando Live Coding...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Live Coding</h1>
              <p className="text-sm text-gray-600">
                {appData?.app_name}
              </p>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              appData?.status === 'ready' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {appData?.status}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={() => setShowFileExplorer(!showFileExplorer)}
              variant="outline"
              size="sm"
            >
              <PanelLeftIcon className="w-4 h-4 mr-2" />
              Archivos
            </Button>
            <Button
              onClick={() => setShowCodePanel(!showCodePanel)}
              variant="outline"
              size="sm"
            >
              <CodeIcon className="w-4 h-4 mr-2" />
              Código
            </Button>
            <Button
              onClick={() => saveFileContent()}
              disabled={!selectedFile || isSaving}
              size="sm"
            >
              <SaveIcon className="w-4 h-4 mr-2" />
              {isSaving ? 'Guardando...' : 'Guardar'}
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* File Explorer (Collapsible) */}
        {showFileExplorer && (
          <div className="w-64 bg-white border-r border-gray-200 shadow-sm overflow-auto">
            <div className="p-3">
              <h3 className="font-semibold mb-2 text-sm">Archivos del Proyecto</h3>
                             <div className="h-full overflow-y-auto">
                 {renderFileTree(files)}
               </div>
            </div>
          </div>
        )}

        {/* Central Preview Area */}
        <div className="flex-1 flex flex-col">
          {/* Preview */}
          <div className="flex-1 p-4">
            <Card className="h-full">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Vista Previa en Tiempo Real</CardTitle>
                  <div className="flex items-center gap-2">
                    {previewUrl && (
                      <a 
                        href={previewUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline"
                      >
                        Abrir en nueva ventana
                      </a>
                    )}
                    <div className={`w-2 h-2 rounded-full ${
                      appData?.status === 'ready' ? 'bg-green-500' : 'bg-yellow-500'
                    }`} />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0 h-full">
                <div className="h-full">
                  {previewUrl ? (
                    <iframe
                      id="preview-iframe"
                      src={previewUrl}
                      className="w-full h-full border-0 rounded-b-lg"
                      title="Preview"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full bg-gray-50 rounded-b-lg">
                      <div className="text-center">
                        <EyeOffIcon className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                        <p className="text-gray-500">Preview no disponible</p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Code Panel (Collapsible) */}
          {showCodePanel && (
            <div className="h-80 border-t bg-white">
              {selectedFile ? (
                <div className="h-full flex flex-col">
                  <div className="p-2 bg-gray-50 border-b flex items-center justify-between">
                    <span className="text-sm font-medium">{selectedFile}</span>
                    <Button
                      onClick={() => setShowCodePanel(false)}
                      variant="ghost"
                      size="sm"
                    >
                      <EyeOffIcon className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="flex-1">
                    <MonacoEditor
                      height="100%"
                      language={getLanguageFromPath(selectedFile)}
                      value={fileContent}
                      onChange={(value: string | undefined) => {
                        if (value !== undefined) {
                          setFileContent(value)
                        }
                      }}
                      options={{
                        minimap: { enabled: false },
                        fontSize: 13,
                        lineNumbers: 'on',
                        roundedSelection: false,
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        theme: 'vs-light'
                      }}
                      onMount={(editor: any) => {
                        editor.addCommand(2097152 + 83, () => {
                          saveFileContent(editor.getValue())
                        })
                      }}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <div className="text-center">
                    <FileIcon className="w-8 h-8 mx-auto mb-2" />
                    <p>Selecciona un archivo para editar</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* AI Agents Chat Panel */}
        <div className="w-80 bg-white border-l border-gray-200 shadow-sm flex flex-col">
          {/* Agent Selection */}
          <div className="p-3 border-b border-gray-200">
            <h3 className="font-semibold text-sm mb-3">Agentes de IA</h3>
            <div className="grid grid-cols-2 gap-2">
              {agents.map((agent) => {
                const IconComponent = agent.icon
                return (
                  <button
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent.id)}
                    className={`p-2 rounded-lg text-xs flex flex-col items-center gap-1 transition-colors ${
                      selectedAgent === agent.id
                        ? 'bg-blue-100 text-blue-700 border-blue-200'
                        : 'hover:bg-gray-50 text-gray-600'
                    }`}
                  >
                    <IconComponent className="w-4 h-4" />
                    <span className="text-xs font-medium">{agent.name}</span>
                  </button>
                )
              })}
            </div>
          </div>

                     {/* Chat Messages */}
           <div className="flex-1 p-3 overflow-y-auto">
            {chatMessages.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <BotIcon className="w-8 h-8 mx-auto mb-2" />
                <p className="text-sm">¿Cómo puedo ayudarte a codificar?</p>
                <p className="text-xs text-gray-400 mt-1">
                  Selecciona un agente y describe lo que necesitas
                </p>
              </div>
            )}
            {chatMessages.map((message, index) => (
              <div
                key={index}
                className={`mb-3 ${
                  message.role === 'user' ? 'text-right' : 'text-left'
                }`}
              >
                <div className="flex items-start gap-2">
                  {message.role === 'assistant' && (
                    <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                      <BotIcon className="w-3 h-3 text-blue-600" />
                    </div>
                  )}
                  <div className="flex-1">
                    <div
                      className={`inline-block p-2 rounded-lg max-w-xs text-sm ${
                        message.role === 'user'
                          ? 'bg-blue-500 text-white ml-auto'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {message.agent && message.role === 'assistant' && (
                        <div className="text-xs opacity-75 mb-1">
                          {agents.find(a => a.id === message.agent)?.name}
                        </div>
                      )}
                      {message.content}
                    </div>
                  </div>
                  {message.role === 'user' && (
                    <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center">
                      <UserIcon className="w-3 h-3 text-gray-600" />
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isGenerating && (
              <div className="text-left mb-3">
                <div className="flex items-start gap-2">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <RefreshCwIcon className="w-3 h-3 text-blue-600 animate-spin" />
                  </div>
                  <div className="inline-block p-2 rounded-lg bg-gray-100 text-sm">
                    Generando respuesta...
                  </div>
                </div>
              </div>
                         )}
           </div>

          {/* Chat Input */}
          <div className="p-3 border-t border-gray-200">
            <div className="flex gap-2">
              <Input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    sendChatMessage()
                  }
                }}
                placeholder={`Pregunta al ${agents.find(a => a.id === selectedAgent)?.name}...`}
                disabled={isGenerating}
                className="text-sm"
              />
              <Button
                onClick={sendChatMessage}
                disabled={isGenerating || !chatInput.trim()}
                size="sm"
              >
                <SendIcon className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Función helper para obtener el lenguaje del archivo
function getLanguageFromPath(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'tsx':
    case 'jsx':
      return 'typescript'
    case 'ts':
      return 'typescript'
    case 'js':
      return 'javascript'
    case 'py':
      return 'python'
    case 'json':
      return 'json'
    case 'md':
      return 'markdown'
    default:
      return 'text'
  }
} 