'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { ChevronDown } from 'lucide-react'

const API_BASE_URL = 'http://localhost:8000'

interface Model {
  id: string
  name: string
}

interface ModelSelectorProps {
  provider: string
  value: string
  onChange: (value: string) => void
  error?: string
}

export default function ModelSelector({ provider, value, onChange, error }: ModelSelectorProps) {
  const [models, setModels] = useState<Model[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchModels = async () => {
      if (!provider) {
        setModels([])
        return
      }

      setLoading(true)
      try {
        const response = await axios.get(`${API_BASE_URL}/models/${provider}`)
        setModels(response.data.models)
        
        // Auto-select first model if current value is not valid
        if (response.data.models.length > 0 && !response.data.models.find((m: Model) => m.id === value)) {
          onChange(response.data.models[0].id)
        }
      } catch (error) {
        console.error('Error fetching models:', error)
        setModels([])
      } finally {
        setLoading(false)
      }
    }

    fetchModels()
  }, [provider, value, onChange])

  const selectedModel = models.find(m => m.id === value)

  if (!provider) {
    return (
      <div className="relative">
        <label className="block text-sm font-medium text-black mb-1">
          Model
        </label>
        <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-black">
          Select a provider first
        </div>
      </div>
    )
  }

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-black mb-1">
        Model
      </label>
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          disabled={loading || models.length === 0}
          className={`w-full px-3 py-2 text-left border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500 text-black ${
            error ? 'border-red-300' : 'border-gray-300'
          }`}
        >
          <span className="block truncate text-black">
            {loading 
              ? 'Loading models...' 
              : selectedModel 
                ? selectedModel.name 
                : models.length === 0 
                  ? 'No models available' 
                  : 'Select model...'
            }
          </span>
          <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </span>
        </button>

        {isOpen && models.length > 0 && (
          <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none">
            {models.map((model) => (
              <button
                key={model.id}
                type="button"
                onClick={() => {
                  onChange(model.id)
                  setIsOpen(false)
                }}
                className={`w-full text-left px-3 py-2 hover:bg-gray-100 ${
                  value === model.id ? 'bg-blue-50 text-blue-600' : 'text-black'
                }`}
              >
                {model.name}
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
