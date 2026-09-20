import { Chip } from './Chip'
import { type ChartInput, SIGN_SHORT, groupByHouse, signForHouse } from './chartUtils'

// Not a grid — a square cut by both diagonals PLUS a diamond connecting the
// four edge midpoints. That produces 4 kite houses (1,4,7,10) at the
// top/left/bottom/right centers, and 8 triangle houses filling the corners.
// Houses are FIXED (H1 is always the top kite); signs rotate into these
// fixed slots based on the ascendant. Verified against a reference diagram.
const NI_LAYOUT: { house: number; left: number; top: number; kite: boolean }[] = [
  { house: 1, left: 50, top: 25, kite: true },
  { house: 2, left: 25, top: 6, kite: false },
  { house: 3, left: 6, top: 25, kite: false },
  { house: 4, left: 25, top: 50, kite: true },
  { house: 5, left: 6, top: 75, kite: false },
  { house: 6, left: 25, top: 94, kite: false },
  { house: 7, left: 50, top: 75, kite: true },
  { house: 8, left: 75, top: 94, kite: false },
  { house: 9, left: 94, top: 75, kite: false },
  { house: 10, left: 75, top: 50, kite: true },
  { house: 11, left: 94, top: 25, kite: false },
  { house: 12, left: 75, top: 6, kite: false },
]

export function NorthIndianChart({ data }: { data: ChartInput }) {
  const byHouse = groupByHouse(data.planets)

  return (
    <div
      className="relative rounded-[10px] overflow-hidden border border-white/8"
      style={{ aspectRatio: '1', background: 'rgba(255,255,255,0.015)' }}
    >
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full">
        <rect x="0" y="0" width="100" height="100" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="0.6" />
        <line x1="0" y1="0" x2="100" y2="100" stroke="rgba(255,255,255,0.09)" strokeWidth="0.5" />
        <line x1="100" y1="0" x2="0" y2="100" stroke="rgba(255,255,255,0.09)" strokeWidth="0.5" />
        <line x1="50" y1="0" x2="100" y2="50" stroke="rgba(255,255,255,0.09)" strokeWidth="0.5" />
        <line x1="100" y1="50" x2="50" y2="100" stroke="rgba(255,255,255,0.09)" strokeWidth="0.5" />
        <line x1="50" y1="100" x2="0" y2="50" stroke="rgba(255,255,255,0.09)" strokeWidth="0.5" />
        <line x1="0" y1="50" x2="50" y2="0" stroke="rgba(255,255,255,0.09)" strokeWidth="0.5" />
      </svg>

      {NI_LAYOUT.map(({ house, left, top, kite }) => {
        const sign = signForHouse(data.ascendant_sign, house)
        const chips = byHouse[house] ?? []
        const isLagna = house === 1
        return (
          <div
            key={house}
            className="absolute flex flex-col items-center text-center leading-tight -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${left}%`, top: `${top}%`, width: kite ? 76 : 50 }}
          >
            <span className="text-[6.5px] tracking-wide text-white/16 font-medium">H{house}</span>
            <span className={`text-[7.5px] tracking-wide mt-px ${isLagna ? 'text-emerald-400/65' : 'text-white/30'}`}>
              {SIGN_SHORT[sign] ?? sign}
            </span>
            {(isLagna || chips.length > 0) && (
              <div className="flex flex-wrap gap-px justify-center mt-0.5">
                {isLagna && <Chip label="As" kind="lagna" />}
                {chips.map(c => <Chip key={c.key} label={c.label} kind={c.kind} />)}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
