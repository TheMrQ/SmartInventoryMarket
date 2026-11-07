import { useCallback, useContext, useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { AlertTriangle, LoaderCircle, PackageCheck, PackageOpen, Search, X } from 'lucide-react'
import { WorkspaceContext } from './workspace-context'

const modalStack = []

export function Badge({ children, tone = 'neutral' }) { return <span className={`badge badge-${tone}`}>{children}</span> }
export function Button({ children, loading, className = '', disabled, ...props }) { return <button className={`button ${className}`} disabled={loading || disabled} {...props}>{loading && <LoaderCircle size={15} className="spin" />}{children}</button> }
export function Empty({ title, children }) { return <div className="empty"><PackageOpen size={28} /><strong>{title}</strong><span>{children}</span></div> }
export function Loading() { return <div className="loading"><span /><span /><span /></div> }
export function SearchField({ value, onChange, label = 'Search', placeholder = 'Search', ariaLabel }) {
  return <label className="search-field"><span>{label}</span><span className="search-control"><Search size={16} aria-hidden="true"/><input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} aria-label={ariaLabel || label}/>{value && <button type="button" className="search-clear" onClick={() => onChange('')} aria-label={`Clear ${label.toLowerCase()}`}><X size={14}/></button>}</span></label>
}
export function ResultCount({ count, label = 'results', detail }) { const text = count === 1 && !label.startsWith('matching ') && label.endsWith('s') ? label.slice(0, -1) : label; return <span className="result-count" aria-live="polite"><b>{count} {text}</b>{detail && <small>{detail}</small>}</span> }
export function QueryError({ queries, title = 'Information could not be loaded' }) {
  const failed = queries.filter((query) => query.isError)
  if (!failed.length) return null
  const message = failed[0].error?.message || 'Check your connection and try again.'
  return <div className="callout" role="alert"><strong>{title}</strong><span>{message}</span><Button className="secondary compact" onClick={() => failed.forEach((query) => query.refetch())}>Try again</Button></div>
}
export function Modal({ title, onClose, children, className = '' }) {
  const { collapsed } = useContext(WorkspaceContext)
  const [modalId] = useState(() => Symbol('modal'))
  useEffect(() => {
    modalStack.push(modalId)
    return () => {
      const index = modalStack.lastIndexOf(modalId)
      if (index >= 0) modalStack.splice(index, 1)
    }
  }, [modalId])
  useEffect(() => {
    const closeOnEscape = (event) => {
      if (event.key === 'Escape' && modalStack.at(-1) === modalId) onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [modalId, onClose])
  useEffect(() => {
    const workspace = document.querySelector('.app-shell')
    if (!workspace) return undefined
    const activeCount = Number(workspace.dataset.modalInertCount || 0) + 1
    workspace.dataset.modalInertCount = String(activeCount)
    workspace.inert = true
    return () => {
      const remaining = Math.max(0, Number(workspace.dataset.modalInertCount || 1) - 1)
      if (remaining) {
        workspace.dataset.modalInertCount = String(remaining)
        return
      }
      delete workspace.dataset.modalInertCount
      workspace.inert = false
    }
  }, [])
  return createPortal(<div className={`modal-backdrop ${collapsed ? 'modal-backdrop-collapsed' : ''}`} role="presentation" onMouseDown={onClose}><section className={`modal ${className}`} role="dialog" aria-modal="true" aria-label={title} onMouseDown={(event) => event.stopPropagation()}><header><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Close dialog"><X size={18} /></button></header>{children}</section></div>, document.body)
}
export function ConfirmationDialog({ title, description, children, confirmLabel, cancelLabel = 'Cancel', onConfirm, onCancel, pending = false, destructive = false, icon: Icon = destructive ? AlertTriangle : PackageCheck }) {
  const close = () => { if (!pending) onCancel() }
  return <Modal title={title} className={`confirmation-dialog ${destructive ? 'confirmation-dialog-danger' : ''}`} onClose={close}><div className="confirmation-dialog-body"><i className="confirmation-dialog-icon" aria-hidden="true"><Icon size={21}/></i><div><p>{description}</p>{children}</div></div><footer className="confirmation-dialog-actions"><Button className="secondary" disabled={pending} onClick={close}>{cancelLabel}</Button><Button className={destructive ? 'danger' : ''} loading={pending} onClick={onConfirm}>{confirmLabel}</Button></footer></Modal>
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
