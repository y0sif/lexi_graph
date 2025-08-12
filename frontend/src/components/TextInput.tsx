'use client'

interface TextInputProps {
  value: string
  onChange: (value: string) => void
  error?: string
}

export default function TextInput({ value, onChange, error }: TextInputProps) {
  return (
    <div>
      <label className="block text-sm font-semibold text-black mb-2">
        📝 Lecture Text
      </label>
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={10}
          className={`w-full px-4 py-4 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white resize-none text-black ${
            error ? 'border-red-300 bg-red-50' : 'border-gray-300'
          }`}
          placeholder="Paste your lecture text here... 

For example:
• Course content from a class
• Educational material
• Research notes
• Any structured text content

Minimum 50 characters required."
        />
        
        {/* Character count badge */}
        <div className="absolute bottom-3 right-3">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
            value.length >= 50 
              ? 'bg-green-100 text-green-800' 
              : value.length > 0 
                ? 'bg-yellow-100 text-yellow-800' 
                : 'bg-gray-100 text-gray-600'
          }`}>
            {value.length} chars {value.length >= 50 && '✓'}
          </span>
        </div>
      </div>
      
      <div className="flex justify-between items-center mt-2">
        {error && (
          <p className="text-sm text-red-600 flex items-center gap-1">
            <span>⚠️</span>
            {error}
          </p>
        )}
        <div className="flex items-center gap-2 ml-auto text-xs text-gray-500">
          {value.length >= 50 ? (
            <span className="text-green-600 font-medium">✓ Ready to process</span>
          ) : (
            <span>Need {50 - value.length} more characters</span>
          )}
        </div>
      </div>
    </div>
  )
}
