import { useState, useRef } from 'react'
import { Upload, X } from 'lucide-react'
import Button from './Button'
import { clsx } from 'clsx'

export interface FileUploadProps {
  accept?: string
  multiple?: boolean
  maxSize?: number // in MB
  onFilesSelected: (files: File[]) => void
  className?: string
  buttonText?: string
  buttonVariant?: 'primary' | 'secondary'
}

const FileUpload = ({
  accept = '*',
  multiple = false,
  maxSize = 100,
  onFilesSelected,
  className,
  buttonText = '选择文件',
  buttonVariant = 'primary',
}: FileUploadProps) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [dragging, setDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFiles = (files: FileList | null): File[] => {
    if (!files) return []

    const validFiles: File[] = []
    const maxSizeBytes = maxSize * 1024 * 1024

    Array.from(files).forEach((file) => {
      if (file.size > maxSizeBytes) {
        alert(`文件 ${file.name} 超过大小限制 (${maxSize}MB)`)
        return
      }
      validFiles.push(file)
    })

    return validFiles
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = validateFiles(e.target.files)
    if (files.length > 0) {
      setSelectedFiles(files)
      onFilesSelected(files)
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(false)

    const files = validateFiles(e.dataTransfer.files)
    if (files.length > 0) {
      setSelectedFiles(files)
      onFilesSelected(files)
    }
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => {
    setDragging(false)
  }

  const removeFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index)
    setSelectedFiles(newFiles)
    onFilesSelected(newFiles)
  }

  const clearFiles = () => {
    setSelectedFiles([])
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className={clsx('space-y-4', className)}>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={clsx(
          'rounded-lg border-2 border-dashed p-8 text-center transition-colors',
          dragging
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
            : 'border-surface-300 hover:border-surface-400 dark:border-surface-700'
        )}
      >
        <Upload className="mx-auto h-12 w-12 text-surface-400" />
        <p className="mt-4 text-sm text-surface-600 dark:text-surface-400">
          拖拽文件到此处，或
        </p>
        <Button
          className="mt-2"
          variant={buttonVariant}
          onClick={() => fileInputRef.current?.click()}
        >
          {buttonText}
        </Button>
        <p className="mt-2 text-xs text-surface-500">
          {accept !== '*' && `支持格式: ${accept}`}
          {maxSize && ` • 最大 ${maxSize}MB`}
        </p>
      </div>

      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">已选择 {selectedFiles.length} 个文件</p>
            <button
              onClick={clearFiles}
              className="text-xs text-surface-500 hover:text-surface-700"
            >
              清除全部
            </button>
          </div>
          <div className="space-y-1">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between rounded-lg bg-surface-100 px-3 py-2 dark:bg-surface-800"
              >
                <div className="flex-1 truncate">
                  <p className="truncate text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-surface-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="ml-2 rounded p-1 hover:bg-surface-200 dark:hover:bg-surface-700"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUpload
