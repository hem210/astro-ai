import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import type { FormEvent } from 'react'
import { api } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const STARS: [number, number, number][] = [
  [5, 15, 1], [12, 82, 2], [20, 45, 1], [28, 63, 1.5], [35, 28, 1],
  [42, 91, 2], [50, 7, 1], [58, 56, 1.5], [65, 33, 1], [72, 78, 2],
  [80, 19, 1], [88, 65, 1.5], [95, 42, 1], [8, 52, 2], [18, 30, 1],
  [30, 75, 1], [45, 18, 2], [55, 88, 1], [68, 48, 1.5], [82, 25, 1],
  [15, 95, 1], [38, 40, 1], [62, 72, 2], [78, 55, 1], [92, 10, 1.5],
  [3, 38, 1], [25, 62, 1], [48, 84, 2], [70, 5, 1], [90, 45, 1],
]

function getApiError(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const e = err as { response?: { data?: { detail?: string } } }
    return e.response?.data?.detail ?? 'Something went wrong'
  }
  return 'Something went wrong'
}

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({})
  const [loading, setLoading] = useState(false)

  function validate(): boolean {
    const e: typeof errors = {}
    if (!email) e.email = 'Required'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = 'Invalid email'
    if (!password) e.password = 'Required'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  async function handleSubmit(ev: FormEvent) {
    ev.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      await login(email, password)
      const { data: birthProfiles } = await api.get('/birth-profiles')
      navigate(birthProfiles.length > 0 ? '/chat' : '/onboarding')
    } catch (err) {
      toast.error(getApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="dark min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: 'oklch(0.10 0 0)' }}
    >
      <style>{`
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .card-appear { animation: fadeUp 0.45s cubic-bezier(0.16,1,0.3,1) forwards; }
      `}</style>

      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        {STARS.map(([top, left, size], i) => (
          <div
            key={i}
            className="absolute rounded-full bg-white"
            style={{ top: `${top}%`, left: `${left}%`, width: size, height: size, opacity: 0.12 + (i % 5) * 0.06 }}
          />
        ))}
      </div>

      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse 70% 60% at 50% 50%, oklch(0.22 0.04 255 / 0.10), transparent)' }}
        aria-hidden="true"
      />

      <div className="card-appear w-full max-w-sm px-4 relative z-10">
        <div className="text-center mb-8">
          <p className="text-amber-400 text-sm tracking-[0.25em] font-medium">✦ ASTRO AI</p>
          <p className="text-white/30 text-xs mt-1.5 tracking-wider">Welcome back</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-white/8 p-7 space-y-5"
          style={{ background: 'oklch(0.16 0 0 / 0.85)', backdropFilter: 'blur(20px)' }}
        >
          <h1 className="text-white text-lg font-semibold tracking-tight">Sign in</h1>

          <div className="space-y-1.5">
            <Label htmlFor="email" className="text-white/50 text-xs tracking-wide">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={e => { setEmail(e.target.value); setErrors(p => ({ ...p, email: undefined })) }}
              placeholder="you@example.com"
              autoComplete="email"
            />
            {errors.email && <p className="text-red-400/80 text-xs">{errors.email}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="password" className="text-white/50 text-xs tracking-wide">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={e => { setPassword(e.target.value); setErrors(p => ({ ...p, password: undefined })) }}
              placeholder="••••••••"
              autoComplete="current-password"
            />
            {errors.password && <p className="text-red-400/80 text-xs">{errors.password}</p>}
          </div>

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Signing in…' : 'Sign in'}
          </Button>

          <p className="text-center text-white/30 text-sm">
            Don't have an account?{' '}
            <Link to="/signup" className="text-amber-400/70 hover:text-amber-400 transition-colors underline underline-offset-2">
              Sign up
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
