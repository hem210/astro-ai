// Shared data shapes + layout math for North/South Indian kundali charts.
// Houses are always numbered relative to the ascendant (1 = lagna).

export const ZODIAC_ORDER = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const

export const SIGN_SHORT: Record<string, string> = {
  Aries: 'Ari', Taurus: 'Tau', Gemini: 'Gem', Cancer: 'Can',
  Leo: 'Leo', Virgo: 'Vir', Libra: 'Lib', Scorpio: 'Sco',
  Sagittarius: 'Sag', Capricorn: 'Cap', Aquarius: 'Aqu', Pisces: 'Pis',
}

export const PLANET_ORDER = [
  'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu',
] as const

export const PLANET_SHORT: Record<string, string> = {
  sun: 'Su', moon: 'Mo', mars: 'Ma', mercury: 'Me', jupiter: 'Ju',
  venus: 'Ve', saturn: 'Sa', rahu: 'Ra', ketu: 'Ke',
}

export interface ChartPlanetInput {
  house: number
  zodiac: string
  retrograde?: boolean
  degree?: number // degree within sign, 0-30 — D1 only, varga charts don't carry one
}

export interface ChartInput {
  ascendant_sign: string
  planets: Record<string, ChartPlanetInput>
}

/** "4.216" (degrees within sign) -> "4°13'" */
export function formatDegree(deg: number): string {
  let d = Math.floor(deg)
  let m = Math.round((deg - d) * 60)
  if (m === 60) { m = 0; d += 1 }
  return `${d}°${String(m).padStart(2, '0')}'`
}

export type ChipKind = 'lagna' | 'moon' | 'retro' | 'default'

export interface ChipData {
  key: string
  label: string
  kind: ChipKind
}

/** Which sign sits in a fixed house slot — North Indian houses are fixed, signs rotate. */
export function signForHouse(ascendantSign: string, house: number): string {
  const ascIdx = ZODIAC_ORDER.indexOf(ascendantSign as (typeof ZODIAC_ORDER)[number])
  if (ascIdx === -1) return ascendantSign
  return ZODIAC_ORDER[(ascIdx + house - 1) % 12]
}

/** Which house number a fixed sign cell currently is — South Indian signs are fixed, houses rotate. */
export function houseForSign(ascendantSign: string, sign: string): number {
  const ascIdx = ZODIAC_ORDER.indexOf(ascendantSign as (typeof ZODIAC_ORDER)[number])
  const signIdx = ZODIAC_ORDER.indexOf(sign as (typeof ZODIAC_ORDER)[number])
  if (ascIdx === -1 || signIdx === -1) return 0
  return ((signIdx - ascIdx + 12) % 12) + 1
}

function toChip(name: string, p: ChartPlanetInput): ChipData {
  const short = PLANET_SHORT[name] ?? name.slice(0, 2)
  if (name === 'moon') return { key: name, label: short, kind: 'moon' }
  if (p.retrograde) return { key: name, label: `${short}℞`, kind: 'retro' }
  return { key: name, label: short, kind: 'default' }
}

/** Planets grouped by house number — for North Indian placement (fixed houses). */
export function groupByHouse(planets: Record<string, ChartPlanetInput>): Record<number, ChipData[]> {
  const out: Record<number, ChipData[]> = {}
  for (const name of PLANET_ORDER) {
    const p = planets[name]
    if (!p) continue
    ;(out[p.house] ??= []).push(toChip(name, p))
  }
  return out
}

/** Planets grouped by sign — for South Indian placement (fixed signs). */
export function groupBySign(planets: Record<string, ChartPlanetInput>): Record<string, ChipData[]> {
  const out: Record<string, ChipData[]> = {}
  for (const name of PLANET_ORDER) {
    const p = planets[name]
    if (!p) continue
    ;(out[p.zodiac] ??= []).push(toChip(name, p))
  }
  return out
}
