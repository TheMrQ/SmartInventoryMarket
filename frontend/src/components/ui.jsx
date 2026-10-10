import { useEffect, useId, useState } from 'react'
import { LoaderCircle, PackageOpen, X } from 'lucide-react'

export function Badge({ children, tone = 'neutral' }) { return <span className={`badge badge-${tone}`}>{children}</span> }
export function Button({ children, loading, className = '', disabled, ...props }) { return <button className={`button ${className}`} disabled={loading || disabled} {...props}>{loading && <LoaderCircle size={15} className="spin" />}{children}</button> }
export function Empty({ title, children }) { return <div className="empty"><PackageOpen size={28} /><strong>{title}</strong><span>{children}</span></div> }
export function Loading() { return <div className="loading"><span /><span /><span /></div> }
export function Modal({ title, onClose, children, className = '' }) {
  useEffect(() => {
    const closeOnEscape = (event) => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [onClose])
  return <div className="modal-backdrop" role="presentation" onMouseDown={onClose}><section className={`modal ${className}`} role="dialog" aria-modal="true" aria-label={title} onMouseDown={(event) => event.stopPropagation()}><header><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Close dialog"><X size={18} /></button></header>{children}</section></div>
}
export function Tooltip({ label, children }) {
  const [open, setOpen] = useState(false)
  const id = useId()
  useEffect(() => {
    const closeOnEscape = (event) => { if (event.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [])
  return <span className="tooltip" data-open={open || undefined} onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)} onFocus={() => setOpen(true)} onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false) }} aria-describedby={open ? id : undefined}>{children}<span id={id} className="tooltip-content" role="tooltip">{label}</span></span>
}
