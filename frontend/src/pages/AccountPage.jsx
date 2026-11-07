import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Camera, KeyRound, Mail, ShieldCheck, Trash2, UserRound } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { UserAvatar } from '../components/UserAvatar'
import { Button, Loading, QueryError } from '../components/ui'

const tell = (error) => toast.error(error.message || 'The change could not be saved.')
const roleLabel = (role) => (role || '').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase())

export default function AccountPage() {
  const client = useQueryClient()
  const picker = useRef(null)
  const account = useQuery({ queryKey: ['auth-me'], queryFn: api.me, staleTime: 300000 })
  const [nameOverride, setNameOverride] = useState(null)
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const user = account.data

  const saveProfile = useMutation({
    mutationFn: api.updateProfile,
    onSuccess: (updated) => { client.setQueryData(['auth-me'], updated); setNameOverride(null); toast.success('Profile information saved.') },
    onError: tell,
  })
  const uploadAvatar = useMutation({
    mutationFn: api.uploadAvatar,
    onSuccess: (updated) => { client.setQueryData(['auth-me'], updated); toast.success('Profile photo updated.') },
    onError: tell,
  })
  const removeAvatar = useMutation({
    mutationFn: api.removeAvatar,
    onSuccess: (updated) => { client.setQueryData(['auth-me'], updated); toast.success('Profile photo removed.') },
    onError: tell,
  })
  const changePassword = useMutation({
    mutationFn: api.changePassword,
    onSuccess: () => { setPasswords({ current_password: '', new_password: '', confirm_password: '' }); toast.success('Password changed. Other sessions were signed out.') },
    onError: tell,
  })

  if (account.isLoading && !user) return <Loading />
  if (account.isError) return <QueryError queries={[account]} title="Account information could not be loaded" />

  const fullName = nameOverride ?? user.full_name
  const submitProfile = (event) => { event.preventDefault(); saveProfile.mutate({ full_name: fullName }) }
  const selectAvatar = (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (file) uploadAvatar.mutate(file)
  }
  const submitPassword = (event) => {
    event.preventDefault()
    if (passwords.new_password !== passwords.confirm_password) return toast.error('New password confirmation does not match.')
    changePassword.mutate({ current_password: passwords.current_password, new_password: passwords.new_password })
  }

  return <div className="stack account-page">
    <header className="page-heading account-heading page-heading-account">
      <div className="page-heading-copy"><i className="page-heading-icon"><UserRound size={19}/></i><div><h2>My Account</h2><p>Manage your profile details and the security of your account.</p></div></div>
    </header>
    <section className="account-identity" aria-label="Account profile">
      <UserAvatar user={user} className="account-avatar" iconSize={34}/>
      <div className="account-identity-copy"><h3>{user.full_name}</h3><p><Mail size={15} aria-hidden="true"/>{user.email}</p><span className="account-role"><ShieldCheck size={14} aria-hidden="true"/>{roleLabel(user.role)}</span></div>
      <div className="account-avatar-actions">
        <input ref={picker} className="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp" onChange={selectAvatar} aria-label="Choose a profile photo" />
        <Button type="button" className="secondary" loading={uploadAvatar.isPending} onClick={() => picker.current?.click()}><Camera size={16}/>Change photo</Button>
        <Button type="button" className="ghost account-remove-avatar" disabled={!user.avatar_url || removeAvatar.isPending} onClick={() => removeAvatar.mutate()}><Trash2 size={15}/>Remove</Button>
        <small>JPEG, PNG, or WEBP up to 3 MB.</small>
      </div>
    </section>
    <div className="account-grid">
      <section className="panel account-panel">
        <header><div><p className="eyebrow">Profile Information</p><h2>Personal details</h2><p>Keep the name shown across this workspace current.</p></div></header>
        <form className="account-form" onSubmit={submitProfile}>
          <label>Full name<input value={fullName} onChange={(event) => setNameOverride(event.target.value)} minLength="2" maxLength="255" required autoComplete="name" /></label>
          <label>Email address<input value={user.email} readOnly aria-readonly="true" /></label>
          <label>Role<input value={roleLabel(user.role)} readOnly aria-readonly="true" /></label>
          <footer><Button type="submit" loading={saveProfile.isPending} disabled={fullName.trim() === user.full_name}>Save profile</Button></footer>
        </form>
      </section>
      <section className="panel account-panel account-security">
        <header><div><p className="eyebrow">Security</p><h2>Password</h2><p>Changing it keeps this session active and signs out other sessions.</p></div><i className="account-section-icon"><KeyRound size={19}/></i></header>
        <form className="account-form" onSubmit={submitPassword}>
          <label>Current password<input type="password" value={passwords.current_password} onChange={(event) => setPasswords({ ...passwords, current_password: event.target.value })} autoComplete="current-password" required /></label>
          <label>New password<input type="password" value={passwords.new_password} onChange={(event) => setPasswords({ ...passwords, new_password: event.target.value })} autoComplete="new-password" minLength="8" maxLength="128" required /></label>
          <label>Confirm new password<input type="password" value={passwords.confirm_password} onChange={(event) => setPasswords({ ...passwords, confirm_password: event.target.value })} autoComplete="new-password" minLength="8" maxLength="128" required /></label>
          <p className="account-help">Use at least 8 characters and one uppercase letter.</p>
          <footer><Button type="submit" loading={changePassword.isPending}>Change password</Button></footer>
        </form>
      </section>
    </div>
  </div>
}
