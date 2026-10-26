import { useEffect } from 'react'

export default function Modal({ open, onClose, title, children, size = 'md' }: any) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (open) document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [open, onClose])

  if (!open) return null

  const sizeClass = size === 'lg' ? 'max-w-2xl' : size === 'xl' ? 'max-w-4xl' : 'max-w-md'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black bg-opacity-70" onClick={onClose}></div>
      <div className={`relative bg-gray-900 border border-gray-700 rounded-lg ${sizeClass} w-full max-h-[90vh] overflow-auto m-4`}>
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  )
}
