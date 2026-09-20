import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { LogOut } from 'lucide-react'
import { api, getApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { ScrollArea } from '@/components/ui/scroll-area'
import { NorthIndianChart } from '@/components/chart/NorthIndianChart'
import { SouthIndianChart } from '@/components/chart/SouthIndianChart'
import { PLANET_ORDER, formatDegree, type ChartInput } from '@/components/chart/chartUtils'

interface BirthProfile {
  id: string
  type: string
  name: string
  birth_place: string
  day: number
  month: number
  year: number
}

interface D1ChartInput extends ChartInput {
  ascendant: number // absolute longitude, 0-360 — used to derive degree-within-sign
}

interface KundaliBundle {
  d1: D1ChartInput
  d9: ChartInput
  d10: ChartInput
  d12: ChartInput
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const DIVISIONS: { key: keyof KundaliBundle; label: string }[] = [
  { key: 'd1', label: 'D1 · Rashi' },
  { key: 'd9', label: 'D9 · Navamsa' },
  { key: 'd10', label: 'D10 · Dashamsha' },
  { key: 'd12', label: 'D12 · Dvadashamsha' },
]

function formatDob(p: BirthProfile): string {
  return `${p.day} ${MONTHS[p.month - 1]} ${p.year}`
}

export default function ChartPage() {
  const navigate = useNavigate()
  const { logout, user } = useAuth()

  const [profile, setProfile] = useState<BirthProfile | null>(null)
  const [bundle, setBundle] = useState<KundaliBundle | null>(null)
  const [loading, setLoading] = useState(true)
  const [division, setDivision] = useState<keyof KundaliBundle>('d1')
  const [style, setStyle] = useState<'north' | 'south'>('north')

  useEffect(() => {
    api.get<BirthProfile[]>('/birth-profiles')
      .then(({ data }) => {
        const primary = data.find(p => p.type === 'primary') ?? null
        setProfile(primary)
        if (!primary) return
        return api.get<KundaliBundle>(`/birth-profiles/${primary.id}/kundali`)
          .then(({ data }) => setBundle(data))
      })
      .catch(err => toast.error(getApiError(err)))
      .finally(() => setLoading(false))
  }, [])

  const chart = bundle?.[division]
  const isD1 = division === 'd1'

  return (
    <div className="dark flex h-screen overflow-hidden flex-col" style={{ background: 'oklch(0.10 0 0)' }}>

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/8 shrink-0">
        <button
          onClick={() => navigate('/')}
          className="text-amber-400 text-xs tracking-[0.2em] font-medium hover:text-amber-300 transition-colors cursor-pointer"
        >
          ✦ ASTRO AI
        </button>
        <div className="flex items-center gap-1">
          <button onClick={() => navigate('/')} className="px-2.5 py-1.5 text-xs text-white/30 hover:text-white/60 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">Home</button>
          <button onClick={() => navigate('/chat')} className="px-2.5 py-1.5 text-xs text-white/30 hover:text-white/60 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">Ask AI</button>
          <button onClick={() => navigate('/best-matches')} className="px-2.5 py-1.5 text-xs text-white/30 hover:text-white/60 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">Best Matches</button>
          <button onClick={() => navigate('/partners')} className="px-2.5 py-1.5 text-xs text-white/30 hover:text-white/60 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">Partners</button>
          <span className="w-px h-3.5 bg-white/10 mx-1.5" />
          <span className="text-white/30 text-sm">{user?.name}</span>
          <button
            onClick={logout}
            title="Sign out"
            className="p-1.5 text-white/20 hover:text-white/50 transition-colors rounded-lg hover:bg-white/5 cursor-pointer"
          >
            <LogOut className="size-3.5" />
          </button>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="px-4 py-8">
          <div className="mx-auto max-w-md">

            {loading && (
              <p className="text-center text-white/25 text-sm py-16">Calculating chart…</p>
            )}

            {!loading && !profile && (
              <div className="text-center py-16">
                <p className="text-white/20 text-sm mb-4">No birth profile set up yet.</p>
                <button
                  onClick={() => navigate('/settings')}
                  className="text-amber-400/70 hover:text-amber-400 text-sm cursor-pointer"
                >
                  Go to settings →
                </button>
              </div>
            )}

            {!loading && profile && !bundle && (
              <div className="text-center py-16">
                <p className="text-white/20 text-sm">Couldn't calculate your chart. Please try again.</p>
              </div>
            )}

            {!loading && profile && chart && (
              <>
                {/* Page title */}
                <div className="mb-6">
                  <p className="text-amber-400 text-[11px] tracking-[0.2em] font-medium mb-1.5">✦ ASTRO AI</p>
                  <h1 className="text-xl font-semibold text-white/90 tracking-tight">Your Chart</h1>
                  <p className="text-[13px] text-white/30 mt-1">
                    {profile.name} · {formatDob(profile)} · {profile.birth_place}
                  </p>
                </div>

                {/* Division tabs */}
                <div className="flex gap-0.5 p-0.5 rounded-lg bg-white/4 mb-3">
                  {DIVISIONS.map(({ key, label }) => (
                    <button
                      key={key}
                      onClick={() => setDivision(key)}
                      className={`flex-1 text-center text-[10px] px-1 py-1.5 rounded-md transition-colors cursor-pointer whitespace-nowrap ${
                        division === key ? 'bg-white/8 text-white/85' : 'text-white/28 hover:text-white/50'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                {/* Style toggle */}
                <div className="flex gap-0.5 p-0.5 rounded-lg bg-white/3 border border-white/5 mb-4">
                  {(['north', 'south'] as const).map(s => (
                    <button
                      key={s}
                      onClick={() => setStyle(s)}
                      className={`flex-1 text-center text-xs px-2 py-1.5 rounded-md transition-colors cursor-pointer ${
                        style === s ? 'bg-white/7 text-white/80' : 'text-white/28 hover:text-white/50'
                      }`}
                    >
                      {s === 'north' ? 'North Indian' : 'South Indian'}
                    </button>
                  ))}
                </div>

                {/* Chart */}
                {style === 'north' ? (
                  <>
                    <div className="text-center mb-2">
                      <span className="text-[10px] font-medium text-white/35">{profile.name}</span>
                      <span className="text-[8.5px] text-white/15 ml-1.5">{formatDob(profile)}</span>
                    </div>
                    <NorthIndianChart data={chart} />
                  </>
                ) : (
                  <SouthIndianChart data={chart} name={profile.name} dob={formatDob(profile)} />
                )}

                {/* Planet table */}
                <table className="w-full mt-5 border-collapse">
                  <thead>
                    <tr>
                      <th className="text-left text-[9.5px] tracking-wide uppercase text-white/18 font-normal pb-1.5">Planet</th>
                      <th className="text-right text-[9.5px] tracking-wide uppercase text-white/18 font-normal pb-1.5">Sign</th>
                      <th className="text-right text-[9.5px] tracking-wide uppercase text-white/18 font-normal pb-1.5">House</th>
                      {isD1 && <th className="text-right text-[9.5px] tracking-wide uppercase text-white/18 font-normal pb-1.5">Degree</th>}
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-t border-white/4">
                      <td className="py-1.5 text-[11px] text-white/70">Ascendant</td>
                      <td className="py-1.5 text-[11px] text-white/45 text-right">{chart.ascendant_sign}</td>
                      <td className="py-1.5 text-[11px] text-white/28 text-right">—</td>
                      {isD1 && (
                        <td className="py-1.5 text-[11px] text-white/45 text-right">
                          {formatDegree((chart as D1ChartInput).ascendant % 30)}
                        </td>
                      )}
                    </tr>
                    {PLANET_ORDER.map(name => {
                      const p = chart.planets[name]
                      if (!p) return null
                      return (
                        <tr key={name} className="border-t border-white/4">
                          <td className="py-1.5 text-[11px] text-white/70 capitalize">{name}</td>
                          <td className="py-1.5 text-[11px] text-white/45 text-right">
                            {p.zodiac}
                            {p.retrograde && <span className="text-red-400/60 text-[9px] ml-1">℞</span>}
                          </td>
                          <td className="py-1.5 text-[11px] text-white/28 text-right">{p.house}</td>
                          {isD1 && (
                            <td className="py-1.5 text-[11px] text-white/45 text-right">
                              {p.degree !== undefined ? formatDegree(p.degree) : '—'}
                            </td>
                          )}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </>
            )}

          </div>
        </div>
      </ScrollArea>
    </div>
  )
}
