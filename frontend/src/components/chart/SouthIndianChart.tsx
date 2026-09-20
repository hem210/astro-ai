import { Chip } from './Chip'
import { type ChartInput, SIGN_SHORT, groupBySign, houseForSign } from './chartUtils'

// Signs are FIXED — Pisces always top-left, running clockwise. Houses rotate
// based on the ascendant, so only the lagna cell gets the diagonal slash.
const SI_LAYOUT: { sign: string; row: number; col: number }[] = [
  { sign: 'Pisces', row: 0, col: 0 },
  { sign: 'Aries', row: 0, col: 1 },
  { sign: 'Taurus', row: 0, col: 2 },
  { sign: 'Gemini', row: 0, col: 3 },
  { sign: 'Cancer', row: 1, col: 3 },
  { sign: 'Leo', row: 2, col: 3 },
  { sign: 'Virgo', row: 3, col: 3 },
  { sign: 'Libra', row: 3, col: 2 },
  { sign: 'Scorpio', row: 3, col: 1 },
  { sign: 'Sagittarius', row: 3, col: 0 },
  { sign: 'Capricorn', row: 2, col: 0 },
  { sign: 'Aquarius', row: 1, col: 0 },
]

export function SouthIndianChart({ data, name, dob }: { data: ChartInput; name?: string; dob?: string }) {
  const bySign = groupBySign(data.planets)

  return (
    <div
      className="grid rounded-[10px] overflow-hidden border border-white/8"
      style={{ aspectRatio: '1', gridTemplateColumns: 'repeat(4, 1fr)', gridTemplateRows: 'repeat(4, 1fr)' }}
    >
      {SI_LAYOUT.map(({ sign, row, col }) => {
        const house = houseForSign(data.ascendant_sign, sign)
        const isLagna = house === 1
        const chips = bySign[sign] ?? []
        return (
          <div
            key={sign}
            className="relative border border-white/5 flex flex-col items-center justify-center p-1 overflow-hidden"
            style={{ gridColumn: `${col + 1} / ${col + 2}`, gridRow: `${row + 1} / ${row + 2}` }}
          >
            <span className="absolute top-1 left-1.5 text-[7.5px] text-white/22 font-medium">{SIGN_SHORT[sign] ?? sign}</span>
            <span className="absolute top-1 right-1.5 text-[7.5px] text-white/12">H{house}</span>
            {isLagna && (
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  background: 'linear-gradient(to top right, transparent calc(50% - 0.5px), rgba(52,211,153,0.25) calc(50% - 0.5px), rgba(52,211,153,0.25) calc(50% + 0.5px), transparent calc(50% + 0.5px))',
                }}
              />
            )}
            <div className="flex flex-wrap gap-px justify-center mt-3">
              {isLagna && <Chip label="As" kind="lagna" />}
              {chips.map(c => <Chip key={c.key} label={c.label} kind={c.kind} />)}
            </div>
          </div>
        )
      })}
      <div
        className="flex flex-col items-center justify-center"
        style={{ gridColumn: '2 / 4', gridRow: '2 / 4', background: 'rgba(255,255,255,0.015)' }}
      >
        {name && <span className="text-[10px] font-medium text-white/35">{name}</span>}
        {dob && <span className="text-[8.5px] text-white/15 mt-0.5">{dob}</span>}
      </div>
    </div>
  )
}
