import { useState } from 'react'

export default function Tooltip({ text, children }: any) {
  const [show, setShow] = useState(false)
  return (
    <div className="relative inline-block" onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      {children}
      {show && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs bg-gray-800 text-white rounded whitespace-nowrap z-50">
          {text}
        </div>
      )}
    </div>
  )
}
