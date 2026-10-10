import { useCallback, useContext, useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { LoaderCircle, PackageOpen, X } from 'lucide-react'
import { WorkspaceContext } from './workspace-context'

export function Badge({ children, tone = 'neutral' }) { return <span className={`badge badge-${tone}`}>{children}</span> }
export function Button({ children, loading, className = '', disabled, ...props }) { return <button className={`button ${className}`} disabled={loading || disabled} {...props}>{loading && <LoaderCircle size={15} className="spin" />}{children}</button> }
export function Empty({ title, children }) { return <div className="empty"><PackageOpen size={28} /><strong>{title}</strong><span>{children}</span></div> }
export function Loading() { return <div className="loading"><span /><span /><span /></div> }
export function Modal({ title, onClose, children, className = '' }) {
  const { collapsed } = useContext(WorkspaceContext)
  useEffect(() => {
    const closeOnEscape = (event) => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [onClose])
  useEffect(() => {
    const workspace = document.querySelector('.app-shell')
    if (!workspace) return undefined
    workspace.inert = true
    return () => { workspace.inert = false }
  }, [])
  return createPortal(<div className={`modal-backdrop ${collapsed ? 'modal-backdrop-collapsed' : ''}`} role="presentation" onMouseDown={onClose}><section className={`modal ${className}`} role="dialog" aria-modal="true" aria-label={title} onMouseDown={(event) => event.stopPropagation()}><header><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Close dialog"><X size={18} /></button></header>{children}</section></div>, document.body)
}
export function Tooltip({ label, children, portal = false, disabled = false }) {
  const [open, setOpen] = useState(false)
  const [position, setPosition] = useState(null)
  const id = useId()
  const triggerRef = useRef(null)
  const updatePosition = useCallback(() => {
    if (!portal || !triggerRef.current) return
    const box = triggerRef.current.getBoundingClientRect()
    setPosition({ left: box.right + 10, top: box.top + box.height / 2 })
  }, [portal])
  useEffect(() => {
    const closeOnEscape = (event) => { if (event.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [])
  useEffect(() => {
    if (!open || !portal) return undefined
    updatePosition()
    window.addEventListener('resize', updatePosition)
    window.addEventListener('scroll', updatePosition, true)
    return () => { window.removeEventListener('resize', updatePosition); window.removeEventListener('scroll', updatePosition, true) }
  }, [open, portal, updatePosition])
  const content = <span id={id} className={`tooltip-content ${portal ? 'tooltip-content-portal' : ''}`} role="tooltip" style={portal && position ? { left: position.left, top: position.top } : undefined}>{label}</span>
  const show = !disabled && open
  return <span ref={triggerRef} className="tooltip" data-open={show || undefined} onMouseEnter={() => { if (!disabled) setOpen(true) }} onMouseLeave={() => setOpen(false)} onFocus={() => { if (!disabled) setOpen(true) }} onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false) }} aria-describedby={show ? id : undefined}>{children}{portal ? show && position && createPortal(content, document.body) : content}</span>
}
