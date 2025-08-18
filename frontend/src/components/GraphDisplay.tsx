'use client'

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Download, Maximize2, X, ChevronDown, ChevronRight } from 'lucide-react'

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : process.env.NEXT_PUBLIC_API_URL || 'https://your-backend-url.onrender.com'

interface GraphDisplayProps {
  graphPath?: string
  summary?: string
  graphData?: string  // base64 encoded image data
}

export default function GraphDisplay({ graphPath, summary, graphData }: GraphDisplayProps) {
  const [imageError, setImageError] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showSummary, setShowSummary] = useState(false)
  const [downloadError, setDownloadError] = useState('')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Handle escape key to close fullscreen
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false)
      }
    }

    if (isFullscreen) {
      document.addEventListener('keydown', handleEscape)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isFullscreen])

  if (!graphPath) {
    return (
      <div className="text-center py-8 text-black">
        No graph generated yet.
      </div>
    )
  }

  // Check if graphData is a direct URL (starts with http) or base64 data
  const isDirectUrl = graphData && graphData.startsWith('http')
  
  const imageUrl = isDirectUrl 
    ? graphData  // Use direct QuickChart URL
    : graphData 
      ? `data:image/png;base64,${graphData}`  // Use base64 data
      : `${API_BASE_URL}/image/${graphPath}`  // Fallback to API endpoint
      
  const downloadUrl = `${API_BASE_URL}/download/${graphPath}`

  const handleDownload = async () => {
    try {
      setDownloadError('')
      
      // If we have a direct URL, download from there
      if (isDirectUrl && graphData) {
        const response = await fetch(graphData)
        
        if (!response.ok) {
          throw new Error(`Download failed: ${response.statusText}`)
        }
        
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${graphPath}.png`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } else {
        // Fallback to backend download endpoint
        const response = await fetch(downloadUrl)
        
        if (!response.ok) {
          throw new Error(`Download failed: ${response.statusText}`)
        }
        
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = graphPath
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Download error:', error)
      setDownloadError(error instanceof Error ? error.message : 'Download failed')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-black">Generated Graph</h3>
        <div className="flex space-x-2">
          <button
            onClick={() => setIsFullscreen(true)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Maximize2 className="h-4 w-4 mr-2" />
            Zoom
          </button>
          <button
            onClick={handleDownload}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Download className="h-4 w-4 mr-2" />
            Download
          </button>
        </div>
      </div>

      {/* Image Preview */}
      <div className="border border-gray-200 rounded-md overflow-hidden">
        {imageError ? (
          <div className="flex flex-col items-center justify-center py-12 text-black">
            <p className="mb-2">Unable to display image preview</p>
            <p className="text-sm">File: {graphPath}</p>
            <p className="text-sm mb-4">You can still download the file using the button above</p>
            <button
              onClick={() => {
                setImageError(false)
                const img = document.querySelector(`img[src="${imageUrl}"]`) as HTMLImageElement
                if (img) img.src = imageUrl + '?t=' + Date.now() // Force reload
              }}
              className="text-blue-600 hover:text-blue-800 text-sm underline"
            >
              Try loading image again
            </button>
          </div>
        ) : (
          <img
            src={imageUrl}
            alt="Generated concept graph"
            className="w-full h-auto max-h-96 object-contain bg-white cursor-pointer"
            onError={() => setImageError(true)}
            onLoad={() => setImageError(false)}
            onClick={() => setIsFullscreen(true)}
          />
        )}
      </div>

      {/* Fullscreen Modal */}
      {isFullscreen && mounted && createPortal(
        <div className="fixed inset-0 bg-black bg-opacity-95 z-[9999] flex items-center justify-center">
          <div className="relative w-[90vw] h-[90vh] flex items-center justify-center">
            <button
              onClick={() => setIsFullscreen(false)}
              className="absolute top-6 right-6 z-10 p-3 bg-white bg-opacity-20 text-white rounded-full hover:bg-opacity-30 transition-all backdrop-blur-sm"
            >
              <X className="h-8 w-8" />
            </button>
            <img
              src={imageUrl}
              alt="Generated concept graph - Fullscreen"
              className="max-w-full max-h-full object-contain"
              onClick={() => setIsFullscreen(false)}
            />
          </div>
        </div>,
        document.body
      )}

      {downloadError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">Download error: {downloadError}</p>
        </div>
      )}

      {/* Summary Section */}
      {summary && (
        <div className="border-t border-gray-200 pt-4">
          <button
            onClick={() => setShowSummary(!showSummary)}
            className="flex items-center justify-between w-full p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors duration-200"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                📄
              </div>
              <div className="text-left">
                <h3 className="text-lg font-medium text-black">Generated Summary</h3>
                <p className="text-sm text-gray-600">AI-generated summary of your content</p>
              </div>
            </div>
            <div className="flex items-center">
              {showSummary ? (
                <ChevronDown className="h-5 w-5 text-gray-500" />
              ) : (
                <ChevronRight className="h-5 w-5 text-gray-500" />
              )}
            </div>
          </button>
          
          {showSummary && (
            <div className="mt-4 p-6 bg-white border border-gray-200 rounded-lg">
              <div className="prose prose-sm max-w-none">
                <p className="text-black leading-relaxed whitespace-pre-wrap">
                  {summary}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
