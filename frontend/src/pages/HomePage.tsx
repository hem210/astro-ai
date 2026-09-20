import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Settings, LogOut, Sparkles, Users, Heart, LayoutGrid } from 'lucide-react'
import { api } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'

interface BirthProfile {
  id: string
  type: string
  name: string
  birth_place: string
  day: number
  month: number
  year: number
}

interface Conversation {
  id: string
  title: string | null
  updated_at: string
}

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

function relativeDate(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString()
}

const FEATURES = [
  {
    label: 'Ask AI',
    desc: 'Chat about your chart — interpretations, dashas, transits',
    path: '/chat',
    Icon: Sparkles,
    accent: 'border-indigo-400/12 hover:border-indigo-400/20',
    iconColor: 'text-indigo-400/60',
  },
  {
    label: 'Your Chart',
    desc: 'North & South Indian kundali — D1, D9, D10, D12 divisional charts',
    path: '/chart',
    Icon: LayoutGrid,
    accent: 'border-sky-400/12 hover:border-sky-400/20',
    iconColor: 'text-sky-400/60',
  },
  {
    label: 'Best Matches',
    desc: 'Ideal nakshatra & rashi combinations based on Ashtakoota',
    path: '/best-matches',
    Icon: Users,
    accent: 'border-amber-400/12 hover:border-amber-400/20',
    iconColor: 'text-amber-400/60',
  },
  {
    label: 'Partners',
    desc: 'Ashtakoota + dosha analysis for saved partner profiles',
    path: '/partners',
    Icon: Heart,
    accent: 'border-rose-400/12 hover:border-rose-400/20',
    iconColor: 'text-rose-400/60',
  },
]

export default function HomePage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [primaryProfile, setPrimaryProfile] = useState<BirthProfile | null | undefined>(undefined)
  const [recentConvs, setRecentConvs] = useState<Conversation[]>([])

  useEffect(() => {
    api.get<BirthProfile[]>('/birth-profiles')
      .then(({ data }) => setPrimaryProfile(data.find(p => p.type === 'primary') ?? null))
      .catch(() => setPrimaryProfile(null))

    api.get<Conversation[]>('/conversations')
      .then(({ data }) => setRecentConvs(data.slice(0, 3)))
      .catch(() => {})
  }, [])

  const initials = user?.name?.charAt(0).toUpperCase() ?? '?'

  return (
    <div className="dark min-h-screen" style={{ background: 'oklch(0.10 0 0)' }}>

      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
        <span className="text-amber-400 text-xs tracking-[0.2em] font-medium">✦ ASTRO AI</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => navigate('/settings')}
            className="p-1.5 text-white/20 hover:text-white/50 transition-colors rounded-lg hover:bg-white/5 cursor-pointer"
          >
            <Settings className="size-3.5" />
          </button>
          <button
            onClick={logout}
            title="Sign out"
            className="p-1.5 text-white/20 hover:text-white/50 transition-colors rounded-lg hover:bg-white/5 cursor-pointer"
          >
            <LogOut className="size-3.5" />
          </button>
        </div>
      </div>

      <div className="max-w-xl mx-auto px-4 py-8">

        {/* Profile chip */}
        {primaryProfile !== undefined && (
          primaryProfile ? (
            <div
              className="flex items-center gap-3 p-3.5 rounded-2xl border border-white/7 mb-8 cursor-pointer hover:border-white/12 transition-colors select-none"
              style={{ background: 'oklch(0.14 0 0)' }}
              onClick={() => navigate('/settings')}
            >
              <div className="w-9 h-9 rounded-full bg-white/6 flex items-center justify-center text-sm font-medium text-white/40 shrink-0">
                {initials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white/80">{primaryProfile.name}</p>
                <p className="text-xs text-white/30 mt-0.5">
                  {primaryProfile.day} {MONTHS[primaryProfile.month - 1]} {primaryProfile.year} · {primaryProfile.birth_place}
                </p>
              </div>
              <span className="text-xs text-white/15 shrink-0">Edit →</span>
            </div>
          ) : (
            <div
              className="p-4 rounded-2xl border border-amber-400/15 mb-8 text-center cursor-pointer hover:border-amber-400/25 transition-colors select-none"
              style={{ background: 'oklch(0.14 0 0)' }}
              onClick={() => navigate('/settings')}
            >
              <p className="text-xs text-amber-400/50 mb-1">No birth profile set up</p>
              <p className="text-xs text-white/25">Go to settings to add your birth details →</p>
            </div>
          )
        )}

        {/* Feature cards */}
        <p className="text-[10px] tracking-[0.15em] text-white/20 uppercase mb-3">Explore</p>
        <div className="grid grid-cols-1 gap-2 mb-8">
          {FEATURES.map(({ label, desc, path, Icon, accent, iconColor }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`flex items-center gap-4 text-left px-4 py-3.5 rounded-2xl border transition-all cursor-pointer ${accent}`}
              style={{ background: 'oklch(0.14 0 0)' }}
            >
              <Icon className={`size-4 shrink-0 ${iconColor}`} />
              <div className="min-w-0">
                <p className="text-sm font-medium text-white/75 mb-0.5">{label}</p>
                <p className="text-xs text-white/30 leading-relaxed">{desc}</p>
              </div>
            </button>
          ))}
        </div>

        {/* Recent conversations */}
        {recentConvs.length > 0 && (
          <>
            <p className="text-[10px] tracking-[0.15em] text-white/20 uppercase mb-3">Recent</p>
            <div className="space-y-0.5">
              {recentConvs.map(conv => (
                <button
                  key={conv.id}
                  onClick={() => navigate(`/chat/${conv.id}`)}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-left hover:bg-white/4 transition-colors cursor-pointer"
                >
                  <span className="text-sm text-white/45 truncate">{conv.title ?? 'Untitled conversation'}</span>
                  <span className="text-xs text-white/18 shrink-0 ml-4">{relativeDate(conv.updated_at)}</span>
                </button>
              ))}
              <button
                onClick={() => navigate('/chat')}
                className="w-full text-center py-2 text-xs text-white/15 hover:text-white/35 transition-colors cursor-pointer"
              >
                All conversations →
              </button>
            </div>
          </>
        )}

      </div>
    </div>
  )
}
