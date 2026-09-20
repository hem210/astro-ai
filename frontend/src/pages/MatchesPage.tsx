import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { LogOut } from 'lucide-react'
import { api, getApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { ScrollArea } from '@/components/ui/scroll-area'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ScoreBreakdown {
  varna: number
  vashya: number
  tara: number
  yoni: number
  graha_maitri: number
  gana: number
  bhakoota: number
  nadi: number
  total: number
}

interface DoshaInfo {
  cancelled: boolean
  cancellation_reason: string | null
}

interface MatchResult {
  rashi: string
  nakshatra: string
  syllables: string[]
  score: ScoreBreakdown
  nadi_dosha: DoshaInfo | null
  bhakoota_dosha: DoshaInfo | null
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const THRESHOLD = 22

const KOOTAS: { key: keyof ScoreBreakdown; label: string; max: number }[] = [
  { key: 'nadi',         label: 'Nadi',       max: 8 },
  { key: 'bhakoota',    label: 'Bhakoota',   max: 7 },
  { key: 'gana',        label: 'Gana',       max: 6 },
  { key: 'graha_maitri',label: 'Graha M.',   max: 5 },
  { key: 'yoni',        label: 'Yoni',       max: 4 },
  { key: 'tara',        label: 'Tara',       max: 3 },
  { key: 'vashya',      label: 'Vashya',     max: 2 },
  { key: 'varna',       label: 'Varna',      max: 1 },
]

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function scoreColorClass(total: number): string {
  if (total >= 28) return 'text-emerald-400'
  if (total >= 18) return 'text-amber-400'
  return 'text-white/30'
}

function barColorClass(total: number): string {
  if (total >= 28) return 'bg-emerald-400'
  if (total >= 18) return 'bg-amber-400'
  return 'bg-white/20'
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function DoshaChip({ dosha, label }: { dosha: DoshaInfo; label: string }) {
  if (dosha.cancelled) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium line-through decoration-amber-400/35"
        style={{ background: 'rgba(250,204,21,0.07)', color: 'rgba(250,204,21,0.55)', border: '1px solid rgba(250,204,21,0.13)' }}>
        {label} Dosha
      </span>
    )
  }
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium"
      style={{ background: 'rgba(248,113,113,0.1)', color: '#f87171', border: '1px solid rgba(248,113,113,0.18)' }}>
      {label} Dosha
    </span>
  )
}

function DoshaNote({ dosha, label }: { dosha: DoshaInfo; label: string }) {
  return (
    <div className="flex items-center gap-1.5 text-[11px] leading-relaxed">
      <span className="text-white/30 font-semibold shrink-0">{label} Dosha</span>
      {dosha.cancelled ? (
        <span className="text-amber-400/50">Cancelled · {dosha.cancellation_reason}</span>
      ) : (
        <span className="text-red-400/60">Present · no cancellation applies</span>
      )}
    </div>
  )
}

function MatchCard({ match, rank, expanded, onToggle }: {
  match: MatchResult
  rank: number
  expanded: boolean
  onToggle: () => void
}) {
  const pct = (match.score.total / 36) * 100
  const isTop = rank <= 3

  return (
    <div
      onClick={onToggle}
      className="rounded-2xl border px-4 py-3 cursor-pointer transition-colors select-none"
      style={{
        background: 'oklch(0.14 0 0)',
        borderColor: expanded ? 'rgba(255,255,255,0.11)' : 'rgba(255,255,255,0.07)',
      }}
    >
      {/* Top row */}
      <div className="flex items-center gap-3">
        {/* Rank */}
        <span className={`text-[11px] w-5 text-right shrink-0 tabular-nums font-medium ${isTop ? 'text-amber-400' : 'text-white/20'}`}>
          {rank}
        </span>

        {/* Identity */}
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-1.5">
            <span className="text-[15px] font-semibold text-white/88">{match.rashi}</span>
            <span className="text-[13px] text-white/38">{match.nakshatra}</span>
          </div>
          <div className="flex items-center flex-wrap gap-2 mt-1">
            <span className="text-[11px] text-white/20 tracking-wide">
              {match.syllables.join(' · ')}
            </span>
            {match.nadi_dosha && <DoshaChip dosha={match.nadi_dosha} label="Nadi" />}
            {match.bhakoota_dosha && <DoshaChip dosha={match.bhakoota_dosha} label="Bhakoota" />}
          </div>
        </div>

        {/* Score */}
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <span className={`text-lg font-bold tabular-nums leading-none ${scoreColorClass(match.score.total)}`}>
            {match.score.total}
            <span className="text-[11px] font-normal text-white/18">/36</span>
          </span>
          <div className="w-[72px] h-0.5 rounded-full bg-white/7 overflow-hidden">
            <div
              className={`h-full rounded-full ${barColorClass(match.score.total)}`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Expanded breakdown */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-white/5">
          {/* Koota row */}
          <div className="flex flex-wrap">
            {KOOTAS.map(({ key, label, max }) => {
              const val = match.score[key] as number
              return (
                <span key={key} className="flex items-baseline gap-1 pr-2.5 mr-0 py-0.5 border-r border-white/6 last:border-r-0">
                  <span className="text-[10px] text-white/22 tracking-wide">{label}</span>
                  <span className={`text-[12px] font-semibold tabular-nums ${val === 0 ? 'text-red-400/75' : 'text-white/65'}`}>{val}</span>
                  <span className="text-[10px] text-white/18">/{max}</span>
                </span>
              )
            })}
          </div>

          {/* Dosha notes */}
          {(match.nadi_dosha || match.bhakoota_dosha) && (
            <div className="mt-2.5 flex flex-col gap-1">
              {match.nadi_dosha && <DoshaNote dosha={match.nadi_dosha} label="Nadi" />}
              {match.bhakoota_dosha && <DoshaNote dosha={match.bhakoota_dosha} label="Bhakoota" />}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// MatchesPage
// ---------------------------------------------------------------------------

export default function MatchesPage() {
  const navigate = useNavigate()
  const { logout, user } = useAuth()

  const [matches, setMatches] = useState<MatchResult[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    api.get<MatchResult[]>('/best-matches')
      .then(({ data }) => setMatches(data))
      .catch(err => toast.error(getApiError(err)))
      .finally(() => setLoading(false))
  }, [])

  function toggleExpanded(i: number) {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  }

  const above = matches.filter(m => m.score.total >= THRESHOLD)
  const below = matches.filter(m => m.score.total < THRESHOLD)

  return (
    <div className="dark flex h-screen overflow-hidden" style={{ background: 'oklch(0.10 0 0)' }}>
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">

        {/* Header bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8 shrink-0">
          <button
            onClick={() => navigate('/')}
            className="text-amber-400 text-xs tracking-[0.2em] font-medium hover:text-amber-300 transition-colors"
          >
            ✦ ASTRO AI
          </button>
          <div className="flex items-center gap-1">
            <button onClick={() => navigate('/')} className="px-2.5 py-1.5 text-xs text-white/30 hover:text-white/60 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">Home</button>
            <button onClick={() => navigate('/chat')} className="px-2.5 py-1.5 text-xs text-white/30 hover:text-white/60 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">Ask AI</button>
            <button onClick={() => navigate('/chart')} className="px-2.5 py-1.5 text-xs text-white/30 hover:text-white/60 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">Chart</button>
            <button onClick={() => navigate('/partners')} className="px-2.5 py-1.5 text-xs text-white/30 hover:text-white/60 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">Partners</button>
            <span className="w-px h-3.5 bg-white/10 mx-1.5" />
            <span className="text-white/30 text-sm">{user?.name}</span>
            <button
              onClick={logout}
              title="Sign out"
              className="p-1.5 text-white/20 hover:text-white/50 transition-colors rounded-lg hover:bg-white/5"
            >
              <LogOut className="size-3.5" />
            </button>
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="px-4 py-8">
            <div className="mx-auto max-w-2xl">

              {/* Page title */}
              <div className="mb-7">
                <p className="text-amber-400 text-[11px] tracking-[0.2em] font-medium mb-1.5">✦ ASTRO AI</p>
                <h1 className="text-xl font-semibold text-white/90 tracking-tight">Best Matches</h1>
                <p className="text-[13px] text-white/30 mt-1">Ranked by Ashtakoota compatibility · tap a card for breakdown</p>
              </div>

              {/* Loading */}
              {loading && (
                <p className="text-center text-white/25 text-sm py-16">Calculating matches…</p>
              )}

              {/* Results */}
              {!loading && matches.length > 0 && (
                <>
                  {/* Above threshold */}
                  <div className="flex flex-col gap-1.5">
                    {above.map((m, i) => (
                      <MatchCard
                        key={`${m.rashi}-${m.nakshatra}`}
                        match={m}
                        rank={i + 1}
                        expanded={expanded.has(i)}
                        onToggle={() => toggleExpanded(i)}
                      />
                    ))}
                  </div>

                  {/* Show more / below threshold */}
                  {below.length > 0 && (
                    <>
                      {!showAll ? (
                        <button
                          onClick={() => setShowAll(true)}
                          className="mt-3 w-full py-3 text-[12px] text-white/18 hover:text-white/40 transition-colors rounded-xl"
                        >
                          Show {below.length} more with lower scores ›
                        </button>
                      ) : (
                        <>
                          <p className="mt-5 mb-2 ml-1 text-[10px] text-white/20 tracking-widest uppercase">
                            Below threshold · score &lt; {THRESHOLD}
                          </p>
                          <div className="flex flex-col gap-1.5">
                            {below.map((m, i) => {
                              const globalIndex = above.length + i
                              return (
                                <MatchCard
                                  key={`${m.rashi}-${m.nakshatra}`}
                                  match={m}
                                  rank={globalIndex + 1}
                                  expanded={expanded.has(globalIndex)}
                                  onToggle={() => toggleExpanded(globalIndex)}
                                />
                              )
                            })}
                          </div>
                          <button
                            onClick={() => setShowAll(false)}
                            className="mt-3 w-full py-3 text-[12px] text-white/18 hover:text-white/40 transition-colors rounded-xl"
                          >
                            Show less ‹
                          </button>
                        </>
                      )}
                    </>
                  )}
                </>
              )}

              {/* No profile state */}
              {!loading && matches.length === 0 && (
                <div className="text-center py-16">
                  <p className="text-white/20 text-sm">No matches found. Make sure you have a primary birth profile set up.</p>
                </div>
              )}

            </div>
          </div>
        </ScrollArea>

      </div>
    </div>
  )
}
