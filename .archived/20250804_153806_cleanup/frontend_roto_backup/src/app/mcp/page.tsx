'use client'

import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'

export default function MCPPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('tools')

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">MCP Protocol</h1>
        <p className="text-gray-600">Model Context Protocol - Manage tools, resources, and prompts</p>
      </div>

      {/* Status Card */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">TauseStack MCP Server</h3>
            <p className="text-sm text-gray-600">Connected via WebSocket</p>
          </div>
          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
            🟢 Connected
          </span>
        </div>
        
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-indigo-600">8</div>
            <div className="text-sm text-gray-500">Tools</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-indigo-600">5</div>
            <div className="text-sm text-gray-500">Resources</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-indigo-600">3</div>
            <div className="text-sm text-gray-500">Prompts</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { key: 'tools', label: '🔧 Tools' },
              { key: 'resources', label: '📁 Resources' },
              { key: 'prompts', label: '💬 Prompts' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`py-4 px-1 text-sm font-medium border-b-2 ${
                  activeTab === tab.key
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'tools' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Available Tools</h3>
              {[
                { name: 'execute_query', desc: 'Execute database queries' },
                { name: 'get_table_schema', desc: 'Get table schema information' },
                { name: 'generate_text', desc: 'Generate text using AI' },
                { name: 'analyze_text', desc: 'Analyze text content' },
                { name: 'create_tenant', desc: 'Create new tenant' },
                { name: 'update_tenant', desc: 'Update tenant configuration' },
                { name: 'upload_file', desc: 'Upload file to storage' },
                { name: 'authenticate_user', desc: 'Authenticate user credentials' }
              ].map((tool, i) => (
                <div key={i} className="p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">{tool.name}</h4>
                      <p className="text-sm text-gray-600">{tool.desc}</p>
                    </div>
                    <button className="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700">
                      Execute
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'resources' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Available Resources</h3>
              {[
                { uri: 'tenant://config', name: 'Tenant Configuration' },
                { uri: 'database://schema', name: 'Database Schema' },
                { uri: 'storage://info', name: 'Storage Information' },
                { uri: 'auth://users', name: 'User Directory' },
                { uri: 'ai://models', name: 'AI Models' }
              ].map((resource, i) => (
                <div key={i} className="p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">{resource.name}</h4>
                      <p className="text-sm text-gray-600">{resource.uri}</p>
                    </div>
                    <button className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                      Read
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'prompts' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Available Prompts</h3>
              {[
                { name: 'system_prompt', desc: 'Generate system prompt for AI' },
                { name: 'code_generation', desc: 'Generate code based on requirements' },
                { name: 'tenant_analysis', desc: 'Analyze tenant performance' }
              ].map((prompt, i) => (
                <div key={i} className="p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">{prompt.name}</h4>
                      <p className="text-sm text-gray-600">{prompt.desc}</p>
                    </div>
                    <button className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700">
                      Use
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
