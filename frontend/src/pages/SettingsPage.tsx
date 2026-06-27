import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeftIcon } from 'lucide-react'
import { api } from '@/api/client'

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

interface UserProfile {
  id: string
  email: string
  name: string
  created_at: string
}

interface BirthProfile {
  id: string
  type: string
  name: string
  day: number
  month: number
  year: number
  hour: number
  minute: number
  birth_place: string
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
      <span className="text-white/40 text-xs tracking-wide">{label}</span>
      <span className="text-white/80 text-sm">{value}</span>
    </div>
  )
}

export default function SettingsPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState<UserProfile | null>(null)
  const [birth, setBirth] = useState<BirthProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get<UserProfile>('/profile'),
      api.get<BirthProfile[]>('/birth-profiles'),
    ])
      .then(([{ data: profile }, { data: profiles }]) => {
        setUser(profile)
        setBirth(profiles.find(p => p.type === 'primary') ?? null)
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="dark min-h-screen" style={{ background: 'oklch(0.10 0 0)' }}>
      <div className="mx-auto max-w-lg px-4 py-10">

        <button
          onClick={() => navigate('/chat')}
          className="flex items-center gap-1.5 text-white/30 hover:text-white/60 text-xs mb-8 transition-colors"
        >
          <ArrowLeftIcon className="size-3" />
          Back to chat
        </button>

        <div className="mb-8">
          <p className="text-amber-400 text-xs tracking-[0.25em] font-medium mb-1">✦ ASTRO AI</p>
          <h1 className="text-white text-xl font-semibold tracking-tight">Profile</h1>
        </div>

        {loading ? (
          <p className="text-white/30 text-sm">Loading…</p>
        ) : (
          <div className="space-y-4">

            <section
              className="rounded-2xl border border-white/8 px-5 py-1"
              style={{ background: 'oklch(0.16 0 0 / 0.85)' }}
            >
              <p className="text-white/25 text-[10px] tracking-widest uppercase pt-4 pb-2">Account</p>
              {user && (
                <>
                  <Row label="Name" value={user.name} />
                  <Row label="Email" value={user.email} />
                  <Row label="Member since" value={new Date(user.created_at).toLocaleDateString()} />
                </>
              )}
            </section>

            <section
              className="rounded-2xl border border-white/8 px-5 py-1"
              style={{ background: 'oklch(0.16 0 0 / 0.85)' }}
            >
              <p className="text-white/25 text-[10px] tracking-widest uppercase pt-4 pb-2">Birth Profile</p>
              {birth ? (
                <>
                  <Row label="Date" value={`${birth.day} ${MONTHS[birth.month - 1]} ${birth.year}`} />
                  <Row label="Time" value={`${String(birth.hour).padStart(2, '0')}:${String(birth.minute).padStart(2, '0')}`} />
                  <Row label="Place" value={birth.birth_place} />
                </>
              ) : (
                <p className="text-white/30 text-sm py-3">No birth profile found.</p>
              )}
            </section>

          </div>
        )}
      </div>
    </div>
  )
}
