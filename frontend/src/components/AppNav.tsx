import { useNavigate } from 'react-router-dom'
import { Home, Sparkles, Users, Heart, LayoutGrid } from 'lucide-react'

export type NavPage = 'home' | 'chat' | 'chart' | 'best-matches' | 'partners'

const NAV_ITEMS: { id: NavPage; label: string; path: string; Icon: React.ElementType }[] = [
  { id: 'home',         label: 'Home',         path: '/',             Icon: Home       },
  { id: 'chat',         label: 'Ask AI',        path: '/chat',         Icon: Sparkles   },
  { id: 'chart',        label: 'Chart',         path: '/chart',        Icon: LayoutGrid },
  { id: 'best-matches', label: 'Best Matches',  path: '/best-matches', Icon: Users      },
  { id: 'partners',     label: 'Partners',      path: '/partners',     Icon: Heart      },
]

export function AppNav({ current }: { current: NavPage }) {
  const navigate = useNavigate()
  return (
    <div className="px-2 py-2 border-b border-white/8">
      {NAV_ITEMS.map(({ id, label, path, Icon }) => (
        <button
          key={id}
          onClick={() => navigate(path)}
          className={[
            'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-colors cursor-pointer',
            current === id
              ? 'text-white/85 bg-white/6'
              : 'text-white/30 hover:text-white/60 hover:bg-white/4',
          ].join(' ')}
        >
          <Icon className="size-3.5 shrink-0" />
          {label}
        </button>
      ))}
    </div>
  )
}
