import { useEffect, useRef } from 'react'
import { SCENE, buildRoom, drawBubble, drawCharacter, drawDesks, seatOf } from '../pixels'
import type { Agent, Approval } from '../types'

type Props = {
  agents: Agent[]
  approvals: Approval[]
  selectedId: string | null
  onSelect: (id: string | null) => void
}

type Char = {
  x: number
  y: number
  tx: number
  ty: number
  moving: boolean
  next: number
}

const SPEED = 26


export default function OfficeCanvas({ agents, approvals, selectedId, onSelect }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chars = useRef(new Map<string, Char>())
  const hover = useRef<string | null>(null)

  const agentsRef = useRef(agents)
  agentsRef.current = agents
  const approvalsRef = useRef(approvals)
  approvalsRef.current = approvals
  const selectedRef = useRef(selectedId)
  selectedRef.current = selectedId

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    ctx.imageSmoothingEnabled = false

    const room = buildRoom()
    const lights: Record<string, number> = {}
    let raf = 0
    let last = -1

    const map = chars.current
    for (const a of agentsRef.current) {
      if (!map.has(a.id)) {
        const seat = seatOf(a)
        map.set(a.id, { x: seat.x, y: seat.y, tx: seat.x, ty: seat.y, moving: false, next: 0 })
      }
    }

    const draw = (t: number) => {
      if (last < 0) last = t
      const dt = Math.min(0.05, (t - last) / 1000)
      last = t

      const waiting = new Set(approvalsRef.current.map((a) => a.agent_id))

      ctx.clearRect(0, 0, SCENE.w, SCENE.h)
      ctx.drawImage(room, 0, 0)

      const list = agentsRef.current
      const drawable: { a: Agent; c: Char }[] = []

      for (const a of list) {
        const c = map.get(a.id)
        if (!c) continue

        const seat = seatOf(a)
        const atHome = Math.hypot(c.x - seat.x, c.y - seat.y) < 2

        if (a.status === 'idle') {
          if (atHome && t > c.next) {
            c.next = t + 5200 + Math.random() * 6500
            if (Math.random() < 0.32) {
              c.tx = Math.max(14, Math.min(306, seat.x + (Math.random() * 2 - 1) * 11))
              c.ty = Math.max(38, Math.min(170, seat.y + (Math.random() * 2 - 1) * 13))
            }
          }
        } else {
          c.tx = seat.x
          c.ty = seat.y
        }

        const dx = c.tx - c.x
        const dy = c.ty - c.y
        const dist = Math.hypot(dx, dy)
        if (dist > 0.9) {
          const step = Math.min(dist, SPEED * dt)
          c.x += (dx / dist) * step
          c.y += (dy / dist) * step
          c.moving = true
        } else {
          c.x = c.tx
          c.y = c.ty
          c.moving = false
        }

        lights[a.id] = a.status === 'working' ? 0.55 + 0.45 * Math.sin(t / 420) : 0
        drawable.push({ a, c })
      }

      drawable.sort((p, q) => p.c.y - q.c.y)

      for (const { a, c } of drawable) {
        const frame = c.moving
          ? Math.floor(t / 130) % 2 === 0
            ? 'walkA'
            : 'walkB'
          : a.status === 'working'
            ? Math.floor(t / 380) % 2 === 0
              ? 'type'
              : 'stand'
            : 'stand'
        drawCharacter(ctx, c.x, c.y, a.palette, frame, false, selectedRef.current === a.id)
      }

      drawDesks(ctx, list, lights)

      for (const { a, c } of drawable) {
        if (a.status === 'blocked') drawBubble(ctx, c.x, c.y, 'block', Math.sin(t / 300))
        else if (waiting.has(a.id)) drawBubble(ctx, c.x, c.y, 'warn', Math.sin(t / 300))
      }

      raf = requestAnimationFrame(draw)
    }

    raf = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(raf)
  }, [])

  const hit = (evt: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return null
    const box = canvas.getBoundingClientRect()
    const x = ((evt.clientX - box.left) / box.width) * SCENE.w
    const y = ((evt.clientY - box.top) / box.height) * SCENE.h
    let best: { id: string; d: number } | null = null
    for (const a of agentsRef.current) {
      const c = chars.current.get(a.id)
      if (!c) continue
      const d = Math.hypot(x - c.x, y - (c.y - 9))
      if (d < 11 && (!best || d < best.d)) best = { id: a.id, d }
    }
    return best?.id ?? null
  }

  return (
    <canvas
      ref={canvasRef}
      width={SCENE.w}
      height={SCENE.h}
      aria-hidden="true"
      onMouseMove={(e) => {
        hover.current = hit(e)
        if (canvasRef.current) canvasRef.current.style.cursor = hover.current ? 'pointer' : 'default'
      }}
      onMouseLeave={() => {
        hover.current = null
      }}
      onClick={(e) => onSelect(hit(e))}
    />
  )
}
