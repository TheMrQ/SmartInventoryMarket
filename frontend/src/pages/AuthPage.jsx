import { useEffect, useRef, useState } from 'react'
import { BarChart3, Eye, EyeOff } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { api } from '../api/client'

const flipDuration = 780

function PasswordField({ disabled, name = 'password', label = 'Password', confirm = false, show, onToggle, onChange, value }) {
  return <label>{label}<span className="password-field"><input name={name} type={show ? 'text' : 'password'} value={value} onChange={onChange} autoComplete="new-password" minLength="8" disabled={disabled} required />{!confirm && <button type="button" disabled={disabled} onClick={onToggle} aria-label={show ? 'Hide password' : 'Show password'}>{show ? <EyeOff size={17} /> : <Eye size={17} />}</button>}</span></label>
}

export default function AuthPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const client = useQueryClient()
  const urlMode = location.pathname === '/register' ? 'register' : 'login'
  const [pendingMode, setPendingMode] = useState(null)
  const [show, setShow] = useState(false)
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState('')
  const loginRef = useRef(null)
  const registerRef = useRef(null)
  const timerRef = useRef(null)
  const initialFocusRef = useRef(true)
  const skipUrlFocusRef = useRef(false)
  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  const face = pendingMode || urlMode
  const flipping = pendingMode !== null
  useEffect(() => () => window.clearTimeout(timerRef.current), [])
  useEffect(() => {
    if (skipUrlFocusRef.current) {
      skipUrlFocusRef.current = false
      return undefined
    }
    const delay = initialFocusRef.current || reducedMotion ? 0 : flipDuration
    initialFocusRef.current = false
    timerRef.current = window.setTimeout(() => (urlMode === 'login' ? loginRef : registerRef).current?.focus(), delay)
    return () => window.clearTimeout(timerRef.current)
  }, [urlMode, reducedMotion])

  const switchFace = (next) => {
    if (flipping || next === face) return
    setShow(false)
    setFormError('')
    window.clearTimeout(timerRef.current)
    setPendingMode(next)
    const navigateAfterFlip = () => {
      skipUrlFocusRef.current = true
      navigate(next === 'login' ? '/login' : '/register', { state: location.state })
      setPendingMode(null)
      window.requestAnimationFrame(() => (next === 'login' ? loginRef : registerRef).current?.focus())
    }
    if (reducedMotion) return navigateAfterFlip()
    timerRef.current = window.setTimeout(navigateAfterFlip, flipDuration)
  }

  const complete = (user, message) => {
    client.setQueryData(['auth-me'], user)
    toast.success(message)
    navigate(location.state?.from || '/', { replace: true })
  }
  const showError = (error) => setFormError(error.message || 'Please review your details and try again.')
  const login = useMutation({ mutationFn: api.login, onSuccess: (user) => complete(user, 'Welcome back'), onError: showError })
  const register = useMutation({ mutationFn: api.register, onSuccess: (user) => complete(user, 'Account created'), onError: showError })
  const passwordChecks = [
    { ok: password.length >= 8, text: 'At least 8 characters' },
    { ok: /[A-Z]/.test(password), text: 'One uppercase letter' },
  ]

  return <main className="auth-page">
    <div className="auth-atmosphere one" /><div className="auth-atmosphere two" />
    <header className="auth-brand"><div className="brand-mark"><BarChart3 size={20} /></div><strong>Smart <span>Inventory</span></strong></header>
    <section className={`auth-coin ${face === 'register' ? 'is-flipped' : ''} ${flipping ? 'is-flipping' : ''}`} aria-live="polite">
      <div className="auth-ring" aria-hidden="true" />
      <div className="auth-card auth-login" aria-hidden={face !== 'login'}>
        <header><p className="eyebrow">Smart Inventory Market</p><h1>Welcome back</h1><p>Make confident stock decisions with demand forecasting.</p></header>
        <form onSubmit={(event) => { event.preventDefault(); setFormError(''); login.mutate(Object.fromEntries(new FormData(event.currentTarget))) }}>
          <label>Email<input ref={loginRef} name="email" type="email" autoComplete="email" disabled={face !== 'login'} required /></label>
          <PasswordField disabled={face !== 'login'} show={show} onToggle={() => setShow(!show)} />
          {face === 'login' && formError && <p className="auth-error" role="alert">{formError}</p>}
          <button className="auth-submit" disabled={login.isPending || face !== 'login'}>{login.isPending ? 'Signing in…' : 'Sign in'}</button>
        </form>
        <button className="auth-switch" type="button" disabled={face !== 'login' || flipping} tabIndex={face === 'login' ? 0 : -1} onClick={() => switchFace('register')}>Create an account</button>
      </div>
      <div className="auth-card auth-register" aria-hidden={face !== 'register'}>
        <header><p className="eyebrow">Smart Inventory Market</p><h1>Create account</h1><p>New accounts start with inventory-staff access.</p></header>
        <form onSubmit={(event) => {
          event.preventDefault(); setFormError('')
          const { confirm_password, ...payload } = Object.fromEntries(new FormData(event.currentTarget))
          if (payload.password !== confirm_password) return setFormError('Passwords do not match.')
          register.mutate(payload)
        }}>
          <label>Display name<input ref={registerRef} name="full_name" autoComplete="name" disabled={face !== 'register'} required /></label>
          <label>Email<input name="email" type="email" autoComplete="email" disabled={face !== 'register'} required /></label>
          <PasswordField disabled={face !== 'register'} show={show} onToggle={() => setShow(!show)} value={password} onChange={(event) => setPassword(event.target.value)} />
          <p className="password-policy">At least 8 characters, including one uppercase letter.</p>
          <ul className="password-rules" aria-label="Password requirements">{passwordChecks.map((rule) => <li className={rule.ok ? 'met' : ''} key={rule.text}>{rule.text}</li>)}</ul>
          <PasswordField disabled={face !== 'register'} name="confirm_password" label="Confirm password" confirm show={show} />
          {face === 'register' && formError && <p className="auth-error" role="alert">{formError}</p>}
          <button className="auth-submit" disabled={register.isPending || face !== 'register'}>{register.isPending ? 'Creating account…' : 'Create account'}</button>
        </form>
        <button className="auth-switch" type="button" disabled={face !== 'register' || flipping} tabIndex={face === 'register' ? 0 : -1} onClick={() => switchFace('login')}>Back to sign in</button>
      </div>
    </section>
  </main>
}
