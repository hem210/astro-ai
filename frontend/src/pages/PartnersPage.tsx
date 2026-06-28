import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'
import { createParser } from 'eventsource-parser'
import type { KeyboardEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { PlusIcon, TrashIcon, SendIcon, LogOut, PencilIcon, RefreshCwIcon } from 'lucide-react'
import { api, fetchSSE } from '@/api/client'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PartnerProfile {
  id: string
  type: string
  name: string
  gender: string
  day: number
  month: number
  year: number
  hour: number
  minute: number
  birth_place: string
  created_at: string
}

interface PartnerFormData {
  name: string
  gender: string
  day: number
  month: number
  year: number
  hour: number
  minute: number
  birth_place: string
}

interface CompatibilityScore {
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

interface CompatibilityState {
  score: CompatibilityScore | null
  conversation_id: string | null
  messages: { id: string; role: 'user' | 'assistant'; content: string }[]
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

async function listPartners(): Promise<PartnerProfile[]> {
  const { data } = await api.get<PartnerProfile[]>('/birth-profiles')
  return data.filter(p => p.type === 'partner')
}

async function createPartner(body: PartnerFormData): Promise<PartnerProfile> {
  const { data } = await api.post<PartnerProfile>('/birth-profiles', { ...body, type: 'partner' })
  return data
}

async function updatePartner(id: string, body: PartnerFormData): Promise<PartnerProfile> {
  const { data } = await api.put<PartnerProfile>(`/birth-profiles/${id}`, body)
  return data
}

async function deletePartner(id: string): Promise<void> {
  await api.delete(`/birth-profiles/${id}`)
}

async function getCompatibility(partnerId: string): Promise<CompatibilityState> {
  const { data } = await api.get<CompatibilityState>(`/compatibility/${partnerId}`)
  return data
}
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

const YEARS = Array.from({ length: 91 }, (_, i) => 2010 - i)

const KOOTAS: { key: keyof CompatibilityScore; label: string; max: number }[] = [
  { key: 'nadi', label: 'Nadi', max: 8 },
  { key: 'bhakoota', label: 'Bhakoota', max: 7 },
  { key: 'gana', label: 'Gana', max: 6 },
  { key: 'graha_maitri', label: 'Graha Maitri', max: 5 },
  { key: 'yoni', label: 'Yoni', max: 4 },
  { key: 'tara', label: 'Tara', max: 3 },
  { key: 'vashya', label: 'Vashya', max: 2 },
  { key: 'varna', label: 'Varna', max: 1 },
]



// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getApiError(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const e = err as { response?: { data?: { detail?: string } } }
    return e.response?.data?.detail ?? 'Something went wrong'
  }
  return 'Something went wrong'
}

function scoreBarColor(val: number, max: number): string {
  if (val === 0) return 'bg-white/10'
  const pct = val / max
  if (pct === 1) return 'bg-emerald-400/80'
  if (pct >= 0.5) return 'bg-amber-400/70'
  return 'bg-rose-400/60'
}

function totalColor(total: number): string {
  if (total >= 27) return 'text-emerald-400'
  if (total >= 18) return 'text-amber-400'
  return 'text-rose-400'
}

function formatBirthDate(p: PartnerProfile): string {
  return `${p.day} ${MONTHS[p.month - 1]} ${p.year} · ${String(p.hour).padStart(2, '0')}:${String(p.minute).padStart(2, '0')} · ${p.birth_place}`
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ScoreTable({ score }: { score: CompatibilityScore }) {
  return (
    <div>
      <div>
        <div className="flex items-baseline gap-2 mb-3">
          <span className={`text-2xl font-semibold tabular-nums ${totalColor(score.total)}`}>
            {score.total}
          </span>
          <span className="text-white/30 text-sm">/36</span>
          <span className="text-white/20 text-xs ml-1">Ashtakoota</span>
        </div>
        <div className="space-y-1.5">
          {KOOTAS.map(({ key, label, max }) => {
            const val = score[key] as number
            return (
              <div key={key} className="flex items-center gap-3">
                <span className="text-white/40 text-xs w-24 shrink-0">{label}</span>
                <span className="text-white/60 text-xs w-7 shrink-0 tabular-nums">{val}/{max}</span>
                <div className="flex-1 h-1 rounded-full bg-white/8">
                  <div
                    className={`h-full rounded-full transition-all ${scoreBarColor(val, max)}`}
                    style={{ width: `${(val / max) * 100}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Partner form (used for both create and edit)
// ---------------------------------------------------------------------------

interface PartnerFormProps {
  open: boolean
  onClose: () => void
  editing: PartnerProfile | null
  onSaved: (partner: PartnerProfile, wasEdit: boolean) => void
}

function PartnerFormDialog({ open, onClose, editing, onSaved }: PartnerFormProps) {
  const [name, setName] = useState('')
  const [gender, setGender] = useState('')
  const [day, setDay] = useState('')
  const [month, setMonth] = useState('')
  const [year, setYear] = useState('')
  const [hour, setHour] = useState('')
  const [minute, setMinute] = useState('')
  const [place, setPlace] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (editing) {
      setName(editing.name)
      setGender(editing.gender)
      setDay(String(editing.day))
      setMonth(String(editing.month))
      setYear(String(editing.year))
      setHour(String(editing.hour))
      setMinute(String(editing.minute))
      setPlace(editing.birth_place)
    } else {
      setName(''); setGender(''); setDay(''); setMonth(''); setYear('')
      setHour(''); setMinute(''); setPlace('')
    }
  }, [editing, open])

  async function handleSubmit() {
    if (!name.trim() || !gender || !day || !month || !year || !hour || !minute || !place.trim()) {
      toast.error('Please fill in all fields')
      return
    }
    setLoading(true)
    const body = {
      name: name.trim(),
      gender,
      day: parseInt(day),
      month: parseInt(month),
      year: parseInt(year),
      hour: parseInt(hour),
      minute: parseInt(minute),
      birth_place: place.trim(),
    }
    try {
      const saved = editing
        ? await updatePartner(editing.id, body)
        : await createPartner(body)
      onSaved(saved, !!editing)
      onClose()
    } catch (err) {
      toast.error(getApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={v => { if (!v) onClose() }}>
      <DialogContent className="dark sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{editing ? 'Edit partner' : 'Add partner'}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-1">
          <div className="space-y-1.5">
            <Label className="text-white/50 text-xs tracking-wide">Name</Label>
            <Input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Partner's name"
              autoComplete="off"
            />
          </div>

          <div className="space-y-1.5">
            <Label className="text-white/50 text-xs tracking-wide">Gender</Label>
            <Select value={gender} onValueChange={setGender}>
              <SelectTrigger className="w-full h-9"><SelectValue placeholder="Select gender" /></SelectTrigger>
              <SelectContent className="dark">
                <SelectItem value="male">Male</SelectItem>
                <SelectItem value="female">Female</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-white/50 text-xs tracking-wide">Birth Date</Label>
            <div className="grid grid-cols-3 gap-2">
              <Select value={day} onValueChange={setDay}>
                <SelectTrigger className="w-full h-9"><SelectValue placeholder="Day" /></SelectTrigger>
                <SelectContent className="dark">
                  {Array.from({ length: 31 }, (_, i) => (
                    <SelectItem key={i + 1} value={String(i + 1)}>{i + 1}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={month} onValueChange={setMonth}>
                <SelectTrigger className="w-full h-9"><SelectValue placeholder="Month" /></SelectTrigger>
                <SelectContent className="dark">
                  {MONTHS.map((m, i) => (
                    <SelectItem key={i} value={String(i + 1)}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={year} onValueChange={setYear}>
                <SelectTrigger className="w-full h-9"><SelectValue placeholder="Year" /></SelectTrigger>
                <SelectContent className="dark">
                  {YEARS.map(y => (
                    <SelectItem key={y} value={String(y)}>{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="text-white/50 text-xs tracking-wide">Birth Time</Label>
            <div className="grid grid-cols-2 gap-2">
              <Select value={hour} onValueChange={setHour}>
                <SelectTrigger className="w-full h-9"><SelectValue placeholder="Hour" /></SelectTrigger>
                <SelectContent className="dark">
                  {Array.from({ length: 24 }, (_, i) => (
                    <SelectItem key={i} value={String(i)}>{String(i).padStart(2, '0')}:00</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={minute} onValueChange={setMinute}>
                <SelectTrigger className="w-full h-9"><SelectValue placeholder="Minute" /></SelectTrigger>
                <SelectContent className="dark">
                  {Array.from({ length: 60 }, (_, i) => (
                    <SelectItem key={i} value={String(i)}>{String(i).padStart(2, '0')}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="text-white/50 text-xs tracking-wide">Birth Place</Label>
            <Input
              value={place}
              onChange={e => setPlace(e.target.value)}
              placeholder="City, Country"
              autoComplete="off"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Saving…' : editing ? 'Save changes' : 'Add partner'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// PartnersPage
// ---------------------------------------------------------------------------

interface Message {
  role: 'user' | 'assistant'
  content: string
  pending?: boolean
}

export default function PartnersPage() {
  const { partnerId } = useParams<{ partnerId?: string }>()
  const navigate = useNavigate()
  const { logout, user } = useAuth()

  const [partners, setPartners] = useState<PartnerProfile[]>([])
  const [partnersLoading, setPartnersLoading] = useState(true)

  const [compat, setCompat] = useState<CompatibilityState | null>(null)
  const [compatLoading, setCompatLoading] = useState(false)

  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [thinking, setThinking] = useState(false)

  const [formOpen, setFormOpen] = useState(false)
  const [editingPartner, setEditingPartner] = useState<PartnerProfile | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [regenerateOpen, setRegenerateOpen] = useState(false)

  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // ── Load partners list ─────────────────────────────────────────────────────

  useEffect(() => {
    listPartners()
      .then(setPartners)
      .catch(() => toast.error('Failed to load partners'))
      .finally(() => setPartnersLoading(false))
  }, [])

  // ── Load compatibility state when partner changes ──────────────────────────

  useEffect(() => {
    if (!partnerId) {
      setCompat(null)
      setMessages([])

      return
    }
    setCompatLoading(true)
    setMessages([])
    getCompatibility(partnerId)
      .then(state => {
        setCompat(state)
        setMessages(state.messages.map(m => ({ role: m.role, content: m.content })))

      })
      .catch(() => {
        toast.error('Failed to load compatibility data')
        navigate('/partners', { replace: true })
      })
      .finally(() => setCompatLoading(false))
  }, [partnerId, navigate])

  // ── Auto-scroll ────────────────────────────────────────────────────────────

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  // ── Auto-resize textarea ───────────────────────────────────────────────────

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [input])

  // ── SSE stream reader ──────────────────────────────────────────────────────

  async function readStream(response: Response, onToken: (t: string) => void, onDone: (convId: string) => void) {
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let firstToken = false

    const parser = createParser({
      onEvent(event) {
        const data = JSON.parse(event.data) as {
          token?: string; error?: string; done?: boolean; conversation_id?: string
        }
        if (data.token) {
          if (!firstToken) { firstToken = true; setThinking(false) }
          onToken(data.token)
        }
        if (data.error) {
          setThinking(false)
          toast.error(data.error)
          setMessages(prev => prev.filter(m => !m.pending))
        }
        if (data.done && data.conversation_id) {
          setMessages(prev => prev.map(m => m.pending ? { ...m, pending: false } : m))
          onDone(data.conversation_id!)
        }
      },
    })

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      parser.feed(decoder.decode(value, { stream: true }))
    }
  }

  // ── Generate analysis ──────────────────────────────────────────────────────

  async function generateAnalysis() {
    if (!partnerId || streaming) return
    setRegenerateOpen(false)
    setStreaming(true)
    setThinking(true)
    setMessages([{ role: 'assistant', content: '', pending: true }])

    try {
      const response = await fetchSSE(`/compatibility/${partnerId}/analyze`, '{}')
      if (!response) return

      await readStream(
        response,
        token => {
          setMessages(prev => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last?.pending) next[next.length - 1] = { ...last, content: last.content + token }
            return next
          })
        },
        _convId => {
          // Refresh compat state to get the score
          getCompatibility(partnerId).then(state => {
            setCompat(state)
          }).catch(() => {})
        },
      )
    } catch (err) {
      toast.error(getApiError(err))
      setMessages([])
    } finally {
      setStreaming(false)
      setThinking(false)
    }
  }

  // ── Send follow-up message ─────────────────────────────────────────────────

  async function sendMessage() {
    const text = input.trim()
    if (!text || streaming || !partnerId) return

    setInput('')
    setStreaming(true)
    setThinking(true)
    setMessages(prev => [
      ...prev,
      { role: 'user', content: text },
      { role: 'assistant', content: '', pending: true },
    ])

    try {
      const response = await fetchSSE(
        `/compatibility/${partnerId}/chat`,
        JSON.stringify({ message: text }),
      )
      if (!response) return

      await readStream(
        response,
        token => {
          setMessages(prev => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last?.pending) next[next.length - 1] = { ...last, content: last.content + token }
            return next
          })
        },
        () => {},
      )
    } catch (err) {
      toast.error(getApiError(err))
      setMessages(prev => prev.filter(m => !m.pending))
    } finally {
      setStreaming(false)
      setThinking(false)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // ── Partner CRUD ───────────────────────────────────────────────────────────

  function handleSaved(saved: PartnerProfile, wasEdit: boolean) {
    if (wasEdit) {
      setPartners(prev => prev.map(p => p.id === saved.id ? saved : p))
      if (partnerId === saved.id && compat?.score) {
        toast.info('Partner updated. Regenerate the analysis to reflect the changes.')
      }
    } else {
      setPartners(prev => [...prev, saved])
      navigate(`/partners/${saved.id}`)
    }
  }

  async function confirmDelete() {
    if (!deleteId) return
    try {
      await deletePartner(deleteId)
      setPartners(prev => prev.filter(p => p.id !== deleteId))
      if (partnerId === deleteId) navigate('/partners', { replace: true })
    } catch (err) {
      toast.error(getApiError(err))
    } finally {
      setDeleteId(null)
    }
  }

  // ── Derived ────────────────────────────────────────────────────────────────

  const selectedPartner = partners.find(p => p.id === partnerId)
  const hasAnalysis = !!(compat?.score && messages.length > 0)

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="dark flex h-screen overflow-hidden" style={{ background: 'oklch(0.10 0 0)' }}>

      {/* ── Sidebar ── */}
      <aside className="flex w-60 shrink-0 flex-col border-r border-white/8" style={{ background: 'oklch(0.13 0 0)' }}>
        <div className="flex items-center px-4 py-4 border-b border-white/8">
          <span className="text-amber-400 text-xs tracking-[0.2em] font-medium">✦ ASTRO AI</span>
        </div>

        <div className="flex border-b border-white/8">
          <button
            onClick={() => navigate('/chat')}
            className="flex-1 py-2.5 text-xs font-medium text-white/30 hover:text-white/60 border-b-2 border-transparent transition-colors"
          >
            My Chat
          </button>
          <button className="flex-1 py-2.5 text-xs font-medium text-white border-b-2 border-amber-400 transition-colors">
            Partners
          </button>
        </div>

        <div className="px-3 py-3">
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start gap-2 text-white/60 hover:text-white border-white/10"
            onClick={() => { setEditingPartner(null); setFormOpen(true) }}
          >
            <PlusIcon className="size-3.5" />
            Add partner
          </Button>
        </div>

        <ScrollArea className="flex-1">
        <nav className="px-2 pb-4 space-y-0.5">
          {partnersLoading && (
            <p className="px-3 py-6 text-center text-sm text-white/20">Loading…</p>
          )}
          {!partnersLoading && partners.length === 0 && (
            <p className="px-3 py-6 text-center text-sm text-white/20">No partners yet</p>
          )}
          {partners.map(partner => (
            <div
              key={partner.id}
              onClick={() => {
                setMessages([])
                navigate(`/partners/${partner.id}`)
              }}
              className={[
                'group flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition-colors cursor-pointer',
                partnerId === partner.id
                  ? 'bg-white/8 text-white'
                  : 'text-white/40 hover:bg-white/5 hover:text-white/70',
              ].join(' ')}
            >
              <p className="truncate text-sm font-medium leading-snug flex-1 min-w-0">{partner.name}</p>
              <div className="ml-2 shrink-0 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-all">
                <button
                  onClick={e => { e.stopPropagation(); setEditingPartner(partner); setFormOpen(true) }}
                  className="p-1 text-white/30 hover:text-white/70 transition-colors"
                >
                  <PencilIcon className="size-3" />
                </button>
                <button
                  onClick={e => { e.stopPropagation(); setDeleteId(partner.id) }}
                  className="p-1 text-white/30 hover:text-red-400 transition-colors"
                >
                  <TrashIcon className="size-3" />
                </button>
              </div>
            </div>
          ))}
        </nav>
        </ScrollArea>

        <div className="flex items-center justify-between px-3 py-3 border-t border-white/8">
          <button
            onClick={() => navigate('/settings')}
            className="flex-1 min-w-0 text-left px-2 py-1.5 rounded-lg text-white/50 hover:text-white hover:bg-white/5 transition-colors truncate text-sm font-medium"
          >
            {user?.name ?? ''}
          </button>
          <button
            onClick={logout}
            title="Sign out"
            className="shrink-0 ml-1 p-1.5 text-white/20 hover:text-white/50 transition-colors rounded-lg hover:bg-white/5"
          >
            <LogOut className="size-3.5" />
          </button>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="flex flex-1 flex-col overflow-hidden">

        {/* No partner selected */}
        {!partnerId && (
          <div className="flex flex-1 items-center justify-center">
            <div className="text-center">
              <p className="text-amber-400/60 text-sm tracking-[0.2em] mb-2">✦</p>
              <p className="text-white/20 text-sm">Select a partner to view compatibility</p>
            </div>
          </div>
        )}

        {/* Partner selected */}
        {partnerId && (
          <>
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/8 shrink-0">
              {selectedPartner ? (
                <div>
                  <h2 className="text-white text-sm font-semibold">{selectedPartner.name}</h2>
                  <p className="text-white/30 text-xs mt-0.5">{formatBirthDate(selectedPartner)}</p>
                </div>
              ) : (
                <div />
              )}
              {hasAnalysis && !streaming && (
                <button
                  onClick={() => setRegenerateOpen(true)}
                  className="flex items-center gap-1.5 text-white/30 hover:text-white/60 text-xs transition-colors"
                >
                  <RefreshCwIcon className="size-3" />
                  Regenerate
                </button>
              )}
            </div>

            {compatLoading && (
              <div className="flex flex-1 items-center justify-center">
                <p className="text-white/30 text-sm">Loading…</p>
              </div>
            )}

            {!compatLoading && (
              <>
                {/* No analysis yet */}
                {!compat?.score && messages.length === 0 && !streaming && (
                  <div className="flex flex-1 items-center justify-center">
                    <div className="text-center">
                      <p className="text-white/20 text-sm mb-4">No compatibility analysis yet</p>
                      <Button onClick={generateAnalysis}>Generate Analysis</Button>
                    </div>
                  </div>
                )}

                {/* Messages — score table scrolls with content */}
                {(messages.length > 0 || streaming) && (
                  <ScrollArea className="flex-1">
                  <div className="px-4 py-6">
                    <div className="mx-auto max-w-2xl space-y-6">
                      {compat?.score && (
                        <div className="rounded-2xl border border-white/8 p-4 mb-2" style={{ background: 'oklch(0.13 0 0)' }}>
                          <ScoreTable score={compat.score} />
                        </div>
                      )}
                      {messages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          {msg.role === 'user' ? (
                            <div
                              className="max-w-[75%] rounded-2xl rounded-tr-sm px-4 py-2.5 text-base text-white"
                              style={{ background: 'oklch(0.22 0 0)' }}
                            >
                              {msg.content}
                            </div>
                          ) : (
                            <div className="prose prose-invert max-w-[85%] text-base text-white/80 leading-relaxed">
                              {msg.content && (
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                  {msg.content}
                                </ReactMarkdown>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                      {thinking && (
                        <div className="flex justify-start">
                          <p className="text-white/30 text-sm italic animate-pulse">Thinking…</p>
                        </div>
                      )}
                      <div ref={bottomRef} />
                    </div>
                  </div>
                  </ScrollArea>
                )}

                {/* Chat input — only shown when analysis exists */}
                {(hasAnalysis || streaming) && (
                  <div className="border-t border-white/8 px-4 py-4 shrink-0">
                    <div className="mx-auto max-w-2xl">
                      <div
                        className="flex items-end gap-2 rounded-2xl border border-white/8 px-4 py-3"
                        style={{ background: 'oklch(0.16 0 0)' }}
                      >
                        <textarea
                          ref={textareaRef}
                          value={input}
                          onChange={e => setInput(e.target.value)}
                          onKeyDown={handleKeyDown}
                          placeholder="Ask about your compatibility…"
                          rows={1}
                          disabled={streaming}
                          className="flex-1 resize-none bg-transparent text-base text-white placeholder:text-white/25 outline-none disabled:opacity-50"
                          style={{ maxHeight: '160px' }}
                        />
                        <Button
                          size="icon"
                          onClick={sendMessage}
                          disabled={!input.trim() || streaming}
                          title="Send message"
                          className="shrink-0 size-8"
                        >
                          <SendIcon className="size-3.5" />
                        </Button>
                      </div>
                      <p className="mt-2 text-center text-[10px] text-white/15">
                        Enter to send · Shift+Enter for new line
                      </p>
                    </div>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </main>

      {/* ── Partner form dialog ── */}
      <PartnerFormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        editing={editingPartner}
        onSaved={handleSaved}
      />

      {/* ── Delete confirmation dialog ── */}
      <Dialog open={!!deleteId} onOpenChange={v => { if (!v) setDeleteId(null) }}>
        <DialogContent className="dark">
          <DialogHeader>
            <DialogTitle>Delete partner?</DialogTitle>
            <DialogDescription>
              This will permanently delete the partner and their compatibility analysis.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button variant="destructive" onClick={confirmDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Regenerate confirmation dialog ── */}
      <Dialog open={regenerateOpen} onOpenChange={setRegenerateOpen}>
        <DialogContent className="dark">
          <DialogHeader>
            <DialogTitle>Generate new analysis?</DialogTitle>
            <DialogDescription>
              A new analysis will be started. Your previous conversation will no longer be shown.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRegenerateOpen(false)}>Cancel</Button>
            <Button onClick={generateAnalysis}>Regenerate</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  )
}
