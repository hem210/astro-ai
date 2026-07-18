import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import { toast } from 'sonner'
import { createParser } from 'eventsource-parser'
import type { KeyboardEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { PlusIcon, TrashIcon, SendIcon, LogOut, MenuIcon } from 'lucide-react'
import { api, fetchSSE, getApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Conversation {
  id: string
  title: string | null
  updated_at: string
}

interface Message {
  id?: string
  role: 'user' | 'assistant'
  content: string
  pending?: boolean
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// ChatPage
// ---------------------------------------------------------------------------

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId?: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const { logout, user } = useAuth()

  const [conversations, setConversations] = useState<Conversation[]>([])
  // convTick increments to trigger sidebar refetch without needing a stable callback ref
  const [convTick, setConvTick] = useState(0)
  const [sidebarError, setSidebarError] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(location.state?.sidebarOpen ?? false)

  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [thinking, setThinking] = useState(false)

  const [quota, setQuota] = useState<{ questions_used: number; questions_limit: number } | null>(null)

  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // ── Load sidebar (async only — no synchronous setState in effect body) ────

  useEffect(() => {
    api.get<Conversation[]>('/conversations')
      .then(({ data }) => { setConversations(data); setSidebarError(false) })
      .catch(() => setSidebarError(true))
  }, [convTick])

  // ── Load quota ────────────────────────────────────────────────────────────

  function fetchQuota() {
    api.get<{ questions_used: number; questions_limit: number }>('/quota')
      .then(({ data }) => setQuota(data))
      .catch(() => {})
  }

  useEffect(() => { fetchQuota() }, [])

  // ── Load messages when conversationId changes ─────────────────────────────
  // No synchronous setState here — clearing is handled by event handlers
  // (newChat, deleteConversation) that navigate away before this effect runs.

  useEffect(() => {
    if (!conversationId) return

    api.get<Message[]>(`/conversations/${conversationId}/messages`)
      .then(({ data }) => setMessages(data))
      .catch(() => {
        toast.error('Failed to load conversation')
        navigate('/chat', { replace: true })
      })
  }, [conversationId, navigate])

  // ── Auto-scroll ───────────────────────────────────────────────────────────

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  // ── Auto-resize textarea ──────────────────────────────────────────────────

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [input])

  // ── Send message ──────────────────────────────────────────────────────────

  const quotaExhausted = quota !== null && quota.questions_used >= quota.questions_limit

  async function sendMessage() {
    const text = input.trim()
    if (!text || streaming || quotaExhausted) return

    setInput('')
    setStreaming(true)
    setThinking(true)

    setMessages(prev => [
      ...prev,
      { role: 'user', content: text },
      { role: 'assistant', content: '', pending: true },
    ])

    let firstToken = false
    const reqBody = JSON.stringify({ message: text, conversation_id: conversationId ?? null })

    try {
      const response = await fetchSSE('/conversations/chat', reqBody)

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let receivedDone = false
      let receivedError = false

      const parser = createParser({
        onEvent(event) {
          const data = JSON.parse(event.data) as {
            token?: string
            error?: string
            done?: boolean
            conversation_id?: string
          }

          if (data.token) {
            if (!firstToken) {
              firstToken = true
              setThinking(false)
            }
            setMessages(prev => {
              const next = [...prev]
              const last = next[next.length - 1]
              if (last?.pending) {
                next[next.length - 1] = { ...last, content: last.content + data.token }
              }
              return next
            })
          }

          if (data.error) {
            receivedError = true
            setThinking(false)
            toast.error(data.error)
            setMessages(prev => prev.filter(m => !m.pending))
          }

          if (data.done && data.conversation_id) {
            receivedDone = true
            setMessages(prev => prev.map(m => m.pending ? { ...m, pending: false } : m))
            if (!conversationId) {
              navigate(`/chat/${data.conversation_id}`, { replace: true })
            }
            setConvTick(t => t + 1)
            fetchQuota()
          }
        },
      })

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        parser.feed(decoder.decode(value, { stream: true }))
      }

      if (!receivedDone && !receivedError) {
        toast.error('Connection interrupted. Please try again.')
        setMessages(prev => prev.map(m => m.pending ? { ...m, pending: false } : m))
      }
    } catch (err) {
      setThinking(false)
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

  // ── New chat ──────────────────────────────────────────────────────────────

  function newChat() {
    setMessages([])
    setInput('')
    setSidebarOpen(false)
    navigate('/chat', { replace: true })
    textareaRef.current?.focus()
  }

  // ── Delete conversation ───────────────────────────────────────────────────

  async function deleteConversation(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    try {
      await api.delete(`/conversations/${id}`)
      setConversations(prev => prev.filter(c => c.id !== id))
      if (conversationId === id) {
        setMessages([])
        navigate('/chat', { replace: true })
      }
    } catch (err) {
      toast.error(getApiError(err))
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="dark flex h-screen overflow-hidden" style={{ background: 'oklch(0.10 0 0)' }}>

      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-30 bg-black/60 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* ── Sidebar ── */}
      <aside
        className={[
          'fixed inset-y-0 left-0 z-40 flex w-72 shrink-0 flex-col border-r border-white/8',
          'transition-transform duration-300 ease-in-out',
          'md:relative md:w-60 md:z-auto md:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        ].join(' ')}
        style={{ background: 'oklch(0.13 0 0)' }}
      >
        <div className="flex items-center px-4 py-4 border-b border-white/8">
          <span className="text-amber-400 text-xs tracking-[0.2em] font-medium">✦ ASTRO AI</span>
        </div>

        <div className="flex border-b border-white/8">
          <button className="flex-1 py-2.5 text-xs font-medium text-white border-b-2 border-amber-400 transition-colors">
            My Chat
          </button>
          <button
            onClick={() => navigate('/partners', { state: { sidebarOpen } })}
            className="flex-1 py-2.5 text-xs font-medium text-white/30 hover:text-white/60 border-b-2 border-transparent transition-colors"
          >
            Partners
          </button>
        </div>

        <div className="px-3 py-3">
          <Button variant="outline" size="sm" className="w-full justify-start gap-2 text-white/60 hover:text-white border-white/10" onClick={newChat}>
            <PlusIcon className="size-3.5" />
            New chat
          </Button>
        </div>

        <ScrollArea className="flex-1">
        <nav className="px-2 pb-4 space-y-0.5">
          {conversations.map(conv => (
            <div
              key={conv.id}
              onClick={() => {
                setMessages([])
                setSidebarOpen(false)
                navigate(`/chat/${conv.id}`)
              }}
              className={[
                'group flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition-colors cursor-pointer',
                conversationId === conv.id
                  ? 'bg-white/8 text-white'
                  : 'text-white/40 hover:bg-white/5 hover:text-white/70',
              ].join(' ')}
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium leading-snug">
                  {conv.title ?? 'New chat'}
                </p>
                <p className="text-xs text-white/25 mt-0.5">{relativeDate(conv.updated_at)}</p>
              </div>
              <button
                onClick={(e) => deleteConversation(conv.id, e)}
                className="ml-2 shrink-0 opacity-100 md:opacity-0 md:group-hover:opacity-100 text-white/30 hover:text-red-400 transition-all"
              >
                <TrashIcon className="size-3" />
              </button>
            </div>
          ))}

          {conversations.length === 0 && !sidebarError && (
            <p className="px-3 py-6 text-center text-sm text-white/20">No conversations yet</p>
          )}
          {conversations.length === 0 && sidebarError && (
            <p className="px-3 py-6 text-center text-xs text-red-400/50">Failed to load</p>
          )}
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

      {/* ── Chat pane ── */}
      <main className="flex flex-1 flex-col overflow-hidden min-w-0">

        {/* Mobile header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-white/8 shrink-0 md:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-white/40 hover:text-white/70 transition-colors"
          >
            <MenuIcon className="size-5" />
          </button>
          <span className="text-amber-400 text-xs tracking-[0.2em] font-medium">✦ ASTRO AI</span>
        </div>

        {/* Conversation title */}
        {conversationId && (() => {
          const title = conversations.find(c => c.id === conversationId)?.title
          return title ? (
            <div className="shrink-0 px-4 py-3 border-b border-white/5">
              <p className="text-white/30 text-sm font-medium truncate max-w-2xl mx-auto text-center">{title}</p>
            </div>
          ) : null
        })()}

        {/* Messages */}
        <ScrollArea className="flex-1">
        <div className="px-4 py-6">
          <div className="mx-auto max-w-2xl space-y-6">

            {messages.length === 0 && !thinking && (
              <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
                <p className="text-amber-400/60 text-sm tracking-[0.2em] mb-2">✦</p>
                <p className="text-white/20 text-sm">Ask me anything about your stars</p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'user' ? (
                  <div
                    className="max-w-[85%] md:max-w-[75%] rounded-2xl rounded-tr-sm px-4 py-2.5 text-base text-white"
                    style={{ background: 'oklch(0.22 0 0)' }}
                  >
                    {msg.content}
                  </div>
                ) : (
                  <div className="prose prose-invert max-w-[90%] md:max-w-[85%] text-base text-white/80 leading-relaxed">
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

        {/* Input */}
        <div className="border-t border-white/8 px-4 py-4">
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
                placeholder={quotaExhausted ? 'Question limit reached' : 'Ask about your chart…'}
                rows={1}
                disabled={streaming || quotaExhausted}
                className="flex-1 resize-none bg-transparent text-base text-white placeholder:text-white/25 outline-none disabled:opacity-50"
                style={{ maxHeight: '160px' }}
              />
              <Button
                size="icon"
                onClick={sendMessage}
                disabled={!input.trim() || streaming || quotaExhausted}
                title="Send message"
                className="shrink-0 size-8"
              >
                <SendIcon className="size-3.5" />
              </Button>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <p className="text-[10px] text-white/15">
                {quotaExhausted ? "You've reached your question limit for this beta." : 'Enter to send · Shift+Enter for new line'}
              </p>
              {quota !== null && (
                <p className={`text-[10px] ${quotaExhausted ? 'text-red-400/50' : 'text-white/20'}`}>
                  {quota.questions_limit - quota.questions_used} of {quota.questions_limit} remaining
                </p>
              )}
            </div>
          </div>
        </div>

      </main>
    </div>
  )
}
