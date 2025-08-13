'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import axios from 'axios'
import { Loader2, AlertCircle, CheckCircle, BookOpen } from 'lucide-react'

import ProviderSelector from './ProviderSelector'
import ModelSelector from './ModelSelector'
import TextInput from './TextInput'
import GraphDisplay from './GraphDisplay'

const API_BASE_URL = 'http://localhost:8000'

const EXAMPLE_LECTURE = `Welcome to this short lecture on Artificial Intelligence. Let's start with the basics. Artificial Intelligence, or AI, refers to the capability of machines to perform tasks that typically require human intelligence—things like understanding language, recognizing images, or making decisions. Within AI, one of the most important and widely used branches is Machine Learning, or ML. Machine Learning is all about teaching computers to learn from data. Instead of programming every rule manually, we feed the machine examples, and it learns patterns or rules from that data on its own.

Machine learning comes in several types. The first is supervised learning, where we train the model using labeled data—that means we give it both the input and the correct output. For example, if we want to train a model to detect spam emails, we show it lots of examples of emails labeled as "spam" or "not spam," and the model learns to predict that label. The second type is unsupervised learning, where the data has no labels at all. The algorithm's job is to find hidden patterns or groupings. A good example here would be clustering customers based on their shopping behavior—without knowing their categories beforehand. Then we have semi-supervised learning, which is a mix of both: it uses a small amount of labeled data and a larger amount of unlabeled data to improve learning accuracy.

Another major category is reinforcement learning. Here, the model—or we call it an agent—learns by interacting with an environment and receiving feedback in the form of rewards or penalties. A classic example is training a robot to walk or teaching an AI to play games like chess or Go. It tries actions, sees the result, and adjusts its behavior over time to maximize rewards.

Now, within machine learning, there's a very powerful subfield called deep learning. Deep learning uses neural networks with many layers, and it has completely transformed what we can do with AI. These deep neural networks are excellent at automatically learning complex features from data, especially in areas like image recognition, speech processing, and natural language understanding. Deep learning is what powers technologies like self-driving cars, facial recognition, and even language models like ChatGPT.

To summarize: AI is the broad field. Machine learning is a subset that lets computers learn from data. And deep learning is a further subset that uses multi-layered neural networks to learn high-level patterns. Each type of learning—supervised, unsupervised, semi-supervised, and reinforcement—has its strengths depending on the problem you're trying to solve. And understanding which one to use is a big part of becoming proficient in AI.`

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
  summary?: string
  error?: string
}

export default function LexiGraphInterface() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState<ProcessResponse | null>(null)
  const resultsRef = useRef<HTMLDivElement>(null)

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

  // Scroll to results when a successful graph is generated
  useEffect(() => {
    if (result && result.success && resultsRef.current) {
      // Small delay to ensure the results section is fully rendered
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        })
      }, 100)
    }
  }, [result])

  const loadExample = useCallback(() => {
    setValue('text', EXAMPLE_LECTURE)
  }, [setValue])

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
              <label className="block text-sm font-semibold text-black mb-2">
                API Key
              </label>
              <input
                type="password"
                {...register('apiKey')}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-black"
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

          {/* Try Example Button */}
          <div className="flex justify-center">
            <button
              type="button"
              onClick={loadExample}
              className="inline-flex items-center px-6 py-3 border border-blue-300 text-base font-medium rounded-xl text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200 shadow-sm hover:shadow-md"
            >
              <BookOpen className="w-5 h-5 mr-2" />
              Try Example Lecture
            </button>
          </div>

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
        <div ref={resultsRef} className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 overflow-hidden">
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
              <GraphDisplay 
                graphPath={result.graph_path} 
                summary={result.summary}
              />
            ) : (
              <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-lg font-semibold text-red-900 mb-2">
                      {result.message}
                    </h3>
                    {result.error && (
                      <div className="text-red-800 bg-red-100 rounded-lg p-3">
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
