import { useState } from 'react'
import { UserRound } from 'lucide-react'
import { assetUrl } from '../api/client'

function initialsFor(name) {
  const initials = (name || '').trim().split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('')
  return initials.toUpperCase()
}

export function UserAvatar({ user, className = '', iconSize = 22 }) {
  const src = assetUrl(user?.avatar_url)
  const [failedSource, setFailedSource] = useState(null)
  const imageFailed = failedSource === src
  const initials = initialsFor(user?.full_name)
  return <span className={`user-avatar ${className}`}>{src && !imageFailed
    ? <img src={src} alt="" onError={() => setFailedSource(src)} />
    : initials ? <span className="user-avatar-initials" aria-hidden="true">{initials}</span> : <UserRound size={iconSize} aria-hidden="true" />}
  </span>
}
