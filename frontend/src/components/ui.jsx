import { LoaderCircle, PackageOpen, X } from 'lucide-react'

export function Badge({ children, tone = 'neutral' }) { return <span className={`badge badge-${tone}`}>{String(children).replaceAll('_', ' ')}</span> }
export function Button({ children, loading, className = '', disabled, ...props }) { return <button className={`button ${className}`} disabled={loading || disabled} {...props}>{loading && <LoaderCircle size={15} className="spin" />}{children}</button> }
export function Empty({ title, children }) { return <div className="empty"><PackageOpen size={28} /><strong>{title}</strong><span>{children}</span></div> }
export function Loading() { return <div className="loading"><span /><span /><span /></div> }
export function Modal({ title, onClose, children }) { return <div className="modal-backdrop" role="presentation" onMouseDown={onClose}><section className="modal" role="dialog" aria-modal="true" aria-label={title} onMouseDown={(event) => event.stopPropagation()}><header><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Close dialog"><X size={18} /></button></header>{children}</section></div> }
