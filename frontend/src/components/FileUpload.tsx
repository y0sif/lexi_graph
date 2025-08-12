'use client'

import { useCallback } from 'react'
import { Upload, FileText, X } from 'lucide-react'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  disabled: boolean
  selectedFile: File | null
}

export default function FileUpload({ onFileSelect, disabled, selectedFile }: FileUploadProps) {
  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // Validate file type
      if (file.type === 'text/plain' || file.name.endsWith('.md') || file.name.endsWith('.txt')) {
        onFileSelect(file)
      } else {
        alert('Please select a .txt or .md file')
      }
    }
  }, [onFileSelect])

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const file = event.dataTransfer.files[0]
    if (file) {
      if (file.type === 'text/plain' || file.name.endsWith('.md') || file.name.endsWith('.txt')) {
        onFileSelect(file)
      } else {
        alert('Please select a .txt or .md file')
      }
    }
  }, [onFileSelect])

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
  }, [])

  const clearFile = useCallback(() => {
    // Reset the file input
    const fileInput = document.getElementById('file-upload') as HTMLInputElement
    if (fileInput) {
      fileInput.value = ''
    }
  }, [])

  return (
    <div className="space-y-4">
      {selectedFile ? (
        <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-md">
          <div className="flex items-center space-x-3">
            <FileText className="h-5 w-5 text-blue-500" />
            <div>
              <p className="text-sm font-medium text-blue-900">{selectedFile.name}</p>
              <p className="text-xs text-blue-700">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={clearFile}
            className="p-1 text-blue-500 hover:text-blue-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className={`relative border-2 border-dashed rounded-md p-6 transition-colors ${
            disabled 
              ? 'border-gray-200 bg-gray-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <div className="text-center">
            <Upload className={`mx-auto h-8 w-8 ${disabled ? 'text-gray-300' : 'text-gray-400'}`} />
            <div className="mt-2">
              <label
                htmlFor="file-upload"
                className={`cursor-pointer text-sm font-medium ${
                  disabled ? 'text-gray-400' : 'text-blue-600 hover:text-blue-500'
                }`}
              >
                Upload a file
              </label>
              <p className="text-xs text-gray-500 mt-1">or drag and drop</p>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              .txt or .md files only
            </p>
          </div>
          
          <input
            id="file-upload"
            name="file-upload"
            type="file"
            accept=".txt,.md"
            onChange={handleFileChange}
            disabled={disabled}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          />
        </div>
      )}
      
      <p className="text-xs text-gray-500">
        File upload will use the provider, model, and API key configured above.
      </p>
    </div>
  )
}
