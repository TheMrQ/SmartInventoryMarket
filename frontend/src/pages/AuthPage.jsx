import { useCallback, useEffect, useRef, useState } from 'react'
import { BarChart3, Eye, EyeOff } from 'lucide-react'
import { FaFacebookF, FaGithub, FaGoogle } from 'react-icons/fa'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { api } from '../api/client'

function PasswordField({ disabled, name = 'password', label = 'Password', confirm = false, show, onToggle, onChange, value, autoComplete = 'new-password' }) {
  return <label className="auth-field">{label}<span className="password-field"><input name={name} type={show ? 'text' : 'password'} value={value} onChange={onChange} autoComplete={autoComplete} minLength="8" disabled={disabled} required />{!confirm && <button type="button" disabled={disabled} onClick={onToggle} aria-label={show ? 'Hide password' : 'Show password'}>{show ? <EyeOff size={17} /> : <Eye size={17} />}</button>}</span></label>
}

function SocialOptions() {
  return <div className="social-options"><p>Other sign-in options <span>(coming soon)</span></p><div><button type="button" disabled aria-label="Google sign-in coming soon"><FaGoogle /></button><button type="button" disabled aria-label="Facebook sign-in coming soon"><FaFacebookF /></button><button type="button" disabled aria-label="GitHub sign-in coming soon"><FaGithub /></button></div></div>
}

function WelcomePanel({ mode, onSwitch, disabled }) {
  const isLogin = mode === 'login'
  return <div className="welcome-content" aria-live="polite"><div className="welcome-orb one" /><div className="welcome-orb two" /><div className="welcome-copy"><p className="welcome-kicker">Smart Inventory Market</p><h1>{isLogin ? 'Hello, Welcome!' : 'Welcome Back!'}</h1><p>{isLogin ? "Don't have an account?" : 'Already have an account?'}</p><button type="button" className="welcome-switch" disabled={disabled} onClick={() => onSwitch(isLogin ? 'register' : 'login')}>{isLogin ? 'Register' : 'Login'}</button></div></div>
}

function LoginForm({ disabled, firstRef, show, onToggle, error, pending, onSubmit }) {
  return <form className="auth-form login-form" onSubmit={onSubmit} aria-hidden={disabled}>
    <div className="form-heading"><p>Smart Inventory Market</p><h2>Sign in</h2><span>Access your inventory workspace.</span></div>
    <label className="auth-field">Email<input ref={firstRef} name="email" type="email" autoComplete="email" disabled={disabled} required /></label>
    <PasswordField disabled={disabled} show={show} onToggle={onToggle} autoComplete="current-password" />
    {error && <p className="auth-error" role="alert">{error}</p>}
    <button className="auth-submit" disabled={disabled || pending}>{pending ? 'Signing in…' : 'Sign in'}</button>
    <SocialOptions />
  </form>
}

function RegisterForm({ disabled, firstRef, show, onToggle, password, onPasswordChange, error, pending, onSubmit }) {
  const rules = [{ ok: password.length >= 8, text: 'At least 8 characters' }, { ok: /[A-Z]/.test(password), text: 'One uppercase letter' }]
  return <form className="auth-form register-form" onSubmit={onSubmit} aria-hidden={disabled}>
    <div className="form-heading"><p>Smart Inventory Market</p><h2>Create account</h2><span>New accounts receive inventory-staff access.</span></div>
    <label className="auth-field">Display name<input ref={firstRef} name="full_name" autoComplete="name" disabled={disabled} required /></label>
    <label className="auth-field">Email<input name="email" type="email" autoComplete="email" disabled={disabled} required /></label>
    <PasswordField disabled={disabled} show={show} onToggle={onToggle} value={password} onChange={onPasswordChange} />
    <div className="password-guidance"><p>At least 8 characters, including one uppercase letter.</p><ul>{rules.map((rule) => <li className={rule.ok ? 'met' : ''} key={rule.text}>{rule.text}</li>)}</ul></div>
    <PasswordField disabled={disabled} name="confirm_password" label="Confirm password" confirm show={show} />
    {error && <p className="auth-error" role="alert">{error}</p>}
    <button className="auth-submit" disabled={disabled || pending}>{pending ? 'Creating account…' : 'Create account'}</button>
    <SocialOptions />
  </form>
}

export default function AuthPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const client = useQueryClient()
  const routeMode = location.pathname === '/register' ? 'register' : 'login'
  const [visibleMode, setVisibleMode] = useState(routeMode)
  const [phase, setPhase] = useState('idle')
  const [show, setShow] = useState(false)
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState('')
  const targetModeRef = useRef(routeMode)
  const loginRef = useRef(null)
  const registerRef = useRef(null)
  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  const compactLayout = window.matchMedia?.('(max-width: 760px), (max-height: 670px)').matches
  const transitioning = phase !== 'idle'

  const focusMode = useCallback((mode) => window.requestAnimationFrame(() => (mode === 'login' ? loginRef : registerRef).current?.focus()), [])
  const startTransition = useCallback((next, updateUrl) => {
    if (transitioning || next === visibleMode) return
    targetModeRef.current = next
    setShow(false)
    setFormError('')
    if (reducedMotion || compactLayout) {
      setVisibleMode(next)
      if (updateUrl) navigate(next === 'login' ? '/login' : '/register', { state: location.state })
      focusMode(next)
      return
    }
    setPhase('expanding')
  }, [compactLayout, focusMode, location.state, navigate, reducedMotion, transitioning, visibleMode])

  useEffect(() => {
    if (!transitioning && routeMode !== visibleMode) {
      const frame = window.requestAnimationFrame(() => startTransition(routeMode, false))
      return () => window.cancelAnimationFrame(frame)
    }
    return undefined
  }, [routeMode, visibleMode, transitioning, startTransition])

  useEffect(() => {
    if (phase !== 'idle') return undefined
    const frame = window.requestAnimationFrame(() => (visibleMode === 'login' ? loginRef : registerRef).current?.focus())
    return () => window.cancelAnimationFrame(frame)
  }, [phase, visibleMode])

  const onGradientTransitionEnd = (event) => {
    if (event.propertyName !== 'width') return
    if (phase === 'expanding') {
      setVisibleMode(targetModeRef.current)
      setPhase('retracting')
      return
    }
    if (phase === 'retracting') {
      const next = targetModeRef.current
      setPhase('idle')
      if (routeMode !== next) navigate(next === 'login' ? '/login' : '/register', { state: location.state })
      focusMode(next)
    }
  }

  const complete = (user, message) => { client.setQueryData(['auth-me'], user); toast.success(message); navigate(location.state?.from || '/', { replace: true }) }
  const onError = (error) => setFormError(error.message || 'Please review your details and try again.')
  const login = useMutation({ mutationFn: api.login, onSuccess: (user) => complete(user, 'Welcome back'), onError })
  const register = useMutation({ mutationFn: api.register, onSuccess: (user) => complete(user, 'Account created'), onError })
  const inactiveLogin = visibleMode !== 'login' || transitioning
  const inactiveRegister = visibleMode !== 'register' || transitioning

  return <main className="auth-page">
    <div className="auth-atmosphere one" /><div className="auth-atmosphere two" />
    <header className="auth-brand"><div className="brand-mark"><BarChart3 size={20} /></div><strong>Smart <span>Inventory</span></strong></header>
    <section className={`auth-shell mode-${visibleMode} phase-${phase}`} aria-live="polite">
      <div className="auth-pane auth-pane-register"><RegisterForm disabled={inactiveRegister} firstRef={registerRef} show={show} onToggle={() => setShow(!show)} password={password} onPasswordChange={(event) => setPassword(event.target.value)} error={visibleMode === 'register' ? formError : ''} pending={register.isPending} onSubmit={(event) => { event.preventDefault(); setFormError(''); const { confirm_password, ...payload } = Object.fromEntries(new FormData(event.currentTarget)); if (payload.password !== confirm_password) return setFormError('Passwords do not match.'); register.mutate(payload) }} /></div>
      <div className="auth-pane auth-pane-login"><LoginForm disabled={inactiveLogin} firstRef={loginRef} show={show} onToggle={() => setShow(!show)} error={visibleMode === 'login' ? formError : ''} pending={login.isPending} onSubmit={(event) => { event.preventDefault(); setFormError(''); login.mutate(Object.fromEntries(new FormData(event.currentTarget))) }} /></div>
      <div className="gradient-overlay" onTransitionEnd={onGradientTransitionEnd}><WelcomePanel mode={visibleMode} onSwitch={(next) => startTransition(next, true)} disabled={transitioning} /></div>
    </section>
  </main>
}
