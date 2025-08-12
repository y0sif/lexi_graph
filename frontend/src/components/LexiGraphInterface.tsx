'use client'

import { useState, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import axios from 'axios'
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react'

import ProviderSelector from './ProviderSelector'
import ModelSelector from './ModelSelector'
import TextInput from './TextInput'
import GraphDisplay from './GraphDisplay'

const API_BASE_URL = 'http://localhost:8000'

const formSchema = z.object({
  text: z.string().min(50, 'Text must be at least 50 characters long'),
  provider: z.string().min(1, 'Please select a provider'),
  model: z.string().min(1, 'Please select a model'),
  apiKey: z.string().min(1, 'API key is required'),
})

type FormData = z.infer<typeof formSchema>

interface ProcessResponse {
  success: boolean
  message: string
  graph_path?: string
  error?: string
}

export default function LexiGraphInterface() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState<ProcessResponse | null>(null)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      provider: 'anthropic',
      model: 'claude-3-5-haiku-20241022',
      apiKey: '',
      text: '',
    },
  })

  const selectedProvider = watch('provider')

  const onSubmit = useCallback(async (data: FormData) => {
    setIsProcessing(true)
    setResult(null)

    try {
      const response = await axios.post<ProcessResponse>(
        `${API_BASE_URL}/process/text`,
        {
          text: data.text,
          provider: data.provider,
          model: data.model,
          api_key: data.apiKey,
        }
      )

      setResult(response.data)
    } catch (error) {
      console.error('Error processing text:', error)
      setResult({
        success: false,
        message: 'Failed to process text',
        error: axios.isAxiosError(error) 
          ? error.response?.data?.detail || error.message 
          : 'Unknown error occurred',
      })
    } finally {
      setIsProcessing(false)
    }
  }, [])

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Configuration Panel */}
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
              ⚙️
            </div>
            Configuration
          </h2>
          <p className="text-blue-100 mt-1">Set up your AI provider and model preferences</p>
        </div>
        
        <form onSubmit={handleSubmit(onSubmit)} className="p-8 space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <ProviderSelector
              value={watch('provider')}
              onChange={(value: string) => setValue('provider', value)}
              error={errors.provider?.message}
            />
            
            <ModelSelector
              provider={selectedProvider}
              value={watch('model')}
              onChange={(value: string) => setValue('model', value)}
              error={errors.model?.message}
            />
            
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                API Key
              </label>
              <input
                type="password"
                {...register('apiKey')}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white"
                placeholder="Enter your API key"
              />
              {errors.apiKey && (
                <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.apiKey.message}
                </p>
              )}
            </div>
          </div>

          {/* Text Input */}
          <TextInput
            value={watch('text')}
            onChange={(value: string) => setValue('text', value)}
            error={errors.text?.message}
          />

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isProcessing}
            className="w-full flex items-center justify-center px-6 py-4 border border-transparent text-lg font-semibold rounded-xl text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            {isProcessing ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-3 h-6 w-6" />
                <span>Processing your text...</span>
              </>
            ) : (
              <>
                <span className="mr-2">✨</span>
                Generate Knowledge Graph
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 overflow-hidden">
          <div className={`px-8 py-6 ${result.success ? 'bg-gradient-to-r from-green-600 to-emerald-600' : 'bg-gradient-to-r from-red-600 to-rose-600'}`}>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
                {result.success ? (
                  <CheckCircle className="h-5 w-5 text-white" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-white" />
                )}
              </div>
              <h2 className="text-2xl font-bold text-white">
                {result.success ? 'Success!' : 'Error Occurred'}
              </h2>
            </div>
            <p className={`mt-1 ${result.success ? 'text-green-100' : 'text-red-100'}`}>
              {result.success ? 'Your knowledge graph has been generated successfully' : 'Something went wrong during processing'}
            </p>
          </div>

          <div className="p-8">
            {result.success ? (
              <GraphDisplay graphPath={result.graph_path} />
            ) : (
              <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-lg font-semibold text-red-800 mb-2">
                      {result.message}
                    </h3>
                    {result.error && (
                      <div className="text-red-700 bg-red-100 rounded-lg p-3">
                        <p className="font-mono text-sm">{result.error}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
