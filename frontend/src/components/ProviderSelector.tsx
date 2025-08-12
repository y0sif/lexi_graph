'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { ChevronDown } from 'lucide-react'

const API_BASE_URL = 'http://localhost:8000'

interface Provider {
  id: string
  name: string
}

interface ProviderSelectorProps {
  value: string
  onChange: (value: string) => void
  error?: string
}

export default function ProviderSelector({ value, onChange, error }: ProviderSelectorProps) {
  const [providers, setProviders] = useState<Provider[]>([])
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/providers`)
        setProviders(response.data.providers)
      } catch (error) {
        console.error('Error fetching providers:', error)
        // Fallback to hardcoded providers
        setProviders([
          { id: 'anthropic', name: 'Anthropic' },
          { id: 'openai', name: 'OpenAI' },
          { id: 'openrouter', name: 'OpenRouter' },
        ])
      }
    }

    fetchProviders()
  }, [])

  const selectedProvider = providers.find(p => p.id === value)

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Provider
      </label>
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={`w-full px-3 py-2 text-left border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            error ? 'border-red-300' : 'border-gray-300'
          }`}
        >
          <span className="block truncate">
            {selectedProvider ? selectedProvider.name : 'Select provider...'}
          </span>
          <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </span>
        </button>

        {isOpen && (
          <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none">
            {providers.map((provider) => (
              <button
                key={provider.id}
                type="button"
                onClick={() => {
                  onChange(provider.id)
                  setIsOpen(false)
                }}
                className={`w-full text-left px-3 py-2 hover:bg-gray-100 ${
                  value === provider.id ? 'bg-blue-50 text-blue-600' : 'text-gray-900'
                }`}
              >
                {provider.name}
              </button>
            ))}
          </div>
        )}
      </div>
      
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}
