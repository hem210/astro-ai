import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import type { FormEvent } from 'react'
import { api } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const STARS: [number, number, number][] = [
  [5, 15, 1], [12, 82, 2], [20, 45, 1], [28, 63, 1.5], [35, 28, 1],
  [42, 91, 2], [50, 7, 1], [58, 56, 1.5], [65, 33, 1], [72, 78, 2],
  [80, 19, 1], [88, 65, 1.5], [95, 42, 1], [8, 52, 2], [18, 30, 1],
  [30, 75, 1], [45, 18, 2], [55, 88, 1], [68, 48, 1.5], [82, 25, 1],
  [15, 95, 1], [38, 40, 1], [62, 72, 2], [78, 55, 1], [92, 10, 1.5],
]

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

const YEARS = Array.from({ length: 91 }, (_, i) => 2010 - i)

function getApiError(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const e = err as { response?: { data?: { detail?: string } } }
    return e.response?.data?.detail ?? 'Something went wrong'
  }
  return 'Something went wrong'
}


export default function OnboardingPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [gender, setGender] = useState('')
  const [day, setDay] = useState('')
  const [month, setMonth] = useState('')
  const [year, setYear] = useState('')
  const [hour, setHour] = useState('')
  const [minute, setMinute] = useState('')
  const [birthPlace, setBirthPlace] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(ev: FormEvent) {
    ev.preventDefault()
    if (!gender || !day || !month || !year || !hour || !minute || !birthPlace.trim()) {
      toast.error('Please fill in all fields')
      return
    }
    setLoading(true)
    try {
      await api.post('/birth-profiles', {
        name: user!.name,
        type: 'primary',
        gender,
        day: parseInt(day),
        month: parseInt(month),
        year: parseInt(year),
        hour: parseInt(hour),
        minute: parseInt(minute),
        birth_place: birthPlace.trim(),
      })
      navigate('/chat')
    } catch (err) {
      toast.error(getApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="dark min-h-screen flex items-center justify-center relative overflow-hidden py-8"
      style={{ background: 'oklch(0.10 0 0)' }}
    >
      <style>{`
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .card-appear { animation: fadeUp 0.5s cubic-bezier(0.16,1,0.3,1) forwards; }
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

      <div className="card-appear w-full max-w-md px-4 relative z-10">
        {/* Constellation decoration */}
        <div className="flex justify-center mb-6">
          <svg width="100" height="48" viewBox="0 0 100 48" fill="none" aria-hidden="true" className="opacity-50">
            <circle cx="12" cy="36" r="2" fill="#F59E0B" />
            <circle cx="36" cy="18" r="2.5" fill="#F59E0B" />
            <circle cx="58" cy="30" r="2" fill="#F59E0B" />
            <circle cx="80" cy="10" r="2" fill="#F59E0B" />
            <circle cx="92" cy="32" r="1.5" fill="#F59E0B" />
            <line x1="12" y1="36" x2="36" y2="18" stroke="#F59E0B" strokeWidth="0.6" strokeOpacity="0.5" />
            <line x1="36" y1="18" x2="58" y2="30" stroke="#F59E0B" strokeWidth="0.6" strokeOpacity="0.5" />
            <line x1="58" y1="30" x2="80" y2="10" stroke="#F59E0B" strokeWidth="0.6" strokeOpacity="0.5" />
            <line x1="80" y1="10" x2="92" y2="32" stroke="#F59E0B" strokeWidth="0.6" strokeOpacity="0.5" />
          </svg>
        </div>

        <div className="text-center mb-8">
          <h1 className="text-white text-2xl font-semibold tracking-tight">Tell us when you were born</h1>
          <p className="text-white/40 text-sm mt-2 leading-relaxed">
            Your birth details help us personalize your cosmic readings.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-white/8 p-5 sm:p-7 space-y-6"
          style={{ background: 'oklch(0.16 0 0 / 0.85)', backdropFilter: 'blur(20px)' }}
        >
          {/* Gender */}
          <div className="space-y-2">
            <Label className="text-white/50 text-xs tracking-wide">Gender</Label>
            <Select value={gender} onValueChange={setGender}>
              <SelectTrigger className="w-full h-9"><SelectValue placeholder="Select gender" /></SelectTrigger>
              <SelectContent className="dark">
                <SelectItem value="male">Male</SelectItem>
                <SelectItem value="female">Female</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Birth date */}
          <div className="space-y-2">
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

          {/* Birth time */}
          <div className="space-y-2">
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

          {/* Birth place */}
          <div className="space-y-1.5">
            <Label htmlFor="birth_place" className="text-white/50 text-xs tracking-wide">Birth Place</Label>
            <Input
              id="birth_place"
              type="text"
              value={birthPlace}
              onChange={e => setBirthPlace(e.target.value)}
              placeholder="City, Country"
              autoComplete="off"
            />
          </div>

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Saving…' : 'Continue'}
          </Button>
        </form>
      </div>
    </div>
  )
}
