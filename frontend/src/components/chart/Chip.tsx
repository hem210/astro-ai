import type { ChipKind } from './chartUtils'

const CHIP_STYLES: Record<ChipKind, string> = {
  default: 'bg-white/7 text-white/60',
  lagna: 'bg-emerald-400/10 text-emerald-400/90',
  moon: 'bg-indigo-400/10 text-indigo-400/90',
  retro: 'bg-red-400/10 text-red-400/75',
}

export function Chip({ label, kind }: { label: string; kind: ChipKind }) {
  return (
    <span className={`inline-flex items-center px-1 py-px rounded text-[8px] font-semibold tracking-wide leading-[1.4] whitespace-nowrap ${CHIP_STYLES[kind]}`}>
      {label}
    </span>
  )
}
