'use client'

import { useState } from 'react'
import { Download, Eye, EyeOff } from 'lucide-react'

const API_BASE_URL = 'http://localhost:8000'

interface GraphDisplayProps {
  graphPath?: string
}

export default function GraphDisplay({ graphPath }: GraphDisplayProps) {
  const [imageError, setImageError] = useState(false)
  const [showPreview, setShowPreview] = useState(true)
  const [downloadError, setDownloadError] = useState('')

  if (!graphPath) {
    return (
      <div className="text-center py-8 text-black">
        No graph generated yet.
      </div>
    )
  }

  // Separate URLs for image display and download
  const imageUrl = `${API_BASE_URL}/image/${graphPath}`
  const downloadUrl = `${API_BASE_URL}/download/${graphPath}`

  const handleDownload = async () => {
    try {
      setDownloadError('')
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
            onClick={() => setShowPreview(!showPreview)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {showPreview ? (
              <>
                <EyeOff className="h-4 w-4 mr-2" />
                Hide Preview
              </>
            ) : (
              <>
                <Eye className="h-4 w-4 mr-2" />
                Show Preview
              </>
            )}
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

      {showPreview && (
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
              className="w-full h-auto max-h-96 object-contain bg-white"
              onError={() => setImageError(true)}
              onLoad={() => setImageError(false)}
            />
          )}
        </div>
      )}

      {downloadError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">Download error: {downloadError}</p>
        </div>
      )}

      <div className="text-sm text-black">
        <p>Graph file: <code className="bg-gray-100 px-1 py-0.5 rounded">{graphPath}</code></p>
      </div>
    </div>
  )
}
