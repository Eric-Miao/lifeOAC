/* The office is drawn at 320×180 and upscaled with pixelated rendering, so every
   coordinate here is a device pixel of the little world. */

import type { Agent, Palette } from './types'

export const SCENE = { w: 320, h: 180 }

const C = {
  wall: '#c9c3b0',
  trim: '#a49c86',
  glass: '#dce9e4',
  frame: '#8b8371',
  floorA: '#d8d4c3',
  floorB: '#d3cfbe',
  rug: '#8f4c43',
  rugEdge: '#793d36',
  desk: '#b98a5e',
  deskEdge: '#8d6440',
  deskTop: '#c69a6b',
  monitor: '#262b2f',
  screen: '#7fae95',
  plant: '#3f6b47',
  plantDark: '#2d5236',
  pot: '#8a5a3c',
  mat: '#b7ab92',
  shadow: 'rgba(60,52,40,0.16)',
}

export const DESK = { w: 24, h: 11 }

/** feet position for an agent's desk: 9px of the body sits behind the desk edge */
export const seatOf = (a: Agent) => ({ x: a.desk_x + 8, y: a.desk_y + 9 })

type Ctx = CanvasRenderingContext2D

const rect = (ctx: Ctx, x: number, y: number, w: number, h: number, color: string) => {
  ctx.fillStyle = color
  ctx.fillRect(x, y, w, h)
}

export function buildRoom(): HTMLCanvasElement {
  const cv = document.createElement('canvas')
  cv.width = SCENE.w
  cv.height = SCENE.h
  const ctx = cv.getContext('2d')!
  ctx.imageSmoothingEnabled = false

  rect(ctx, 0, 0, SCENE.w, 26, C.wall)
  rect(ctx, 0, 24, SCENE.w, 2, C.trim)

  for (const x of [22, 88, 154, 220]) {
    rect(ctx, x, 6, 52, 13, C.frame)
    rect(ctx, x + 1, 7, 50, 11, C.glass)
    rect(ctx, x + 1, 7, 50, 3, '#eaf2ee')
    rect(ctx, x + 26, 7, 1, 11, C.frame)
  }

  for (let y = 26; y < SCENE.h; y += 8) {
    for (let x = 0; x < SCENE.w; x += 8) {
      const odd = ((x / 8) & 1) ^ ((y / 8) & 1)
      rect(ctx, x, y, 8, 8, odd ? C.floorA : C.floorB)
    }
  }

  // meeting rug + table, tucked into the bottom-right corner
  rect(ctx, 210, 120, 84, 42, C.rugEdge)
  rect(ctx, 211, 121, 82, 40, C.rug)
  rect(ctx, 222, 128, 60, 26, C.deskEdge)
  rect(ctx, 222, 128, 60, 23, C.deskTop)
  rect(ctx, 222, 128, 60, 3, '#d2a97b')
  // chairs
  rect(ctx, 230, 120, 9, 6, '#6f5a44')
  rect(ctx, 252, 120, 9, 6, '#6f5a44')
  rect(ctx, 230, 156, 9, 6, '#6f5a44')
  rect(ctx, 252, 156, 9, 6, '#6f5a44')
  // papers on the table
  rect(ctx, 228, 133, 6, 4, '#efeade')
  rect(ctx, 266, 140, 8, 5, '#efeade')

  // entry mat
  rect(ctx, 6, 158, 30, 20, C.mat)
  rect(ctx, 6, 158, 30, 2, '#a2967d')

  // plants against the wall
  for (const [x, y] of [
    [6, 30],
    [296, 30],
  ]) {
    rect(ctx, x + 2, y + 14, 10, 8, C.pot)
    rect(ctx, x, y + 2, 14, 13, C.plantDark)
    rect(ctx, x + 2, y, 10, 12, C.plant)
    rect(ctx, x + 5, y - 3, 4, 6, C.plant)
  }

  return cv
}

/* ---------- characters ---------- */

const SPRITE = { w: 12, h: 18 }

const STAND = [
  '....hhhh....',
  '...hhhhhh...',
  '..hhhhhhhh..',
  '..hssssssh..',
  '..hsessesh..',
  '..hssssssh..',
  '...ssssss...',
  '....tttt....',
  '..cccccccc..',
  '..cccccccc..',
  '.accccccca.',
  '.accccccca.',
  '..cccccccc..',
  '...pppppp...',
  '...pppppp...',
  '...pp..pp...',
  '...pp..pp...',
  '...bb..bb...',
]

const WALK_A = [...STAND.slice(0, 16), '..pp....pp..', '..bb....bb..']
const WALK_B = [...STAND.slice(0, 16), '...p....p...', '..bb....bb..']
const TYPE = [
  ...STAND.slice(0, 10),
  '..cccccccc..',
  '.accccccca.',
  '..cccccccc..',
  ...STAND.slice(13),
]

export type Frame = 'stand' | 'walkA' | 'walkB' | 'type'

const FRAMES: Record<Frame, string[]> = { stand: STAND, walkA: WALK_A, walkB: WALK_B, type: TYPE }

const cache = new Map<string, HTMLCanvasElement>()

export function sprite(palette: Palette, frame: Frame, flip: boolean): HTMLCanvasElement {
  const key = `${palette.shirt}|${palette.hair}|${frame}|${flip}`
  const hit = cache.get(key)
  if (hit) return hit

  const cv = document.createElement('canvas')
  cv.width = SPRITE.w
  cv.height = SPRITE.h
  const ctx = cv.getContext('2d')!
  ctx.imageSmoothingEnabled = false

  const map: Record<string, string> = {
    h: palette.hair,
    s: palette.skin,
    e: '#221d1a',
    c: palette.shirt,
    p: palette.pants,
    b: '#2a2a2a',
    t: palette.trim,
    a: palette.skin,
  }

  const rows = FRAMES[frame]
  for (let y = 0; y < rows.length; y++) {
    const row = rows[y]
    for (let x = 0; x < row.length; x++) {
      const ch = row[x]
      if (ch === '.') continue
      ctx.fillStyle = map[ch] ?? '#000'
      ctx.fillRect(flip ? SPRITE.w - 1 - x : x, y, 1, 1)
    }
  }
  cache.set(key, cv)
  return cv
}

export function drawCharacter(
  ctx: Ctx,
  x: number,
  y: number,
  palette: Palette,
  frame: Frame,
  flip: boolean,
  selected: boolean,
) {
  // contact shadow
  ctx.fillStyle = C.shadow
  ctx.fillRect(Math.round(x) - 5, Math.round(y) - 1, 10, 2)

  const img = sprite(palette, frame, flip)
  ctx.drawImage(img, Math.round(x) - 6, Math.round(y) - SPRITE.h)

  if (selected) {
    ctx.fillStyle = '#a9352b'
    ctx.fillRect(Math.round(x) - 6, Math.round(y) + 1, 3, 1)
    ctx.fillRect(Math.round(x) + 3, Math.round(y) + 1, 3, 1)
  }
}

export function drawBubble(ctx: Ctx, x: number, y: number, kind: 'warn' | 'block', wobble: number) {
  const bx = Math.round(x) - 5
  const by = Math.round(y) - SPRITE.h - 11 + (wobble > 0.5 ? 0 : -1)
  rect(ctx, bx + 1, by, 8, 8, 'rgba(0,0,0,0.12)')
  rect(ctx, bx, by, 8, 8, '#faf9f3')
  rect(ctx, bx, by, 8, 1, '#3a3f38')
  rect(ctx, bx, by + 7, 8, 1, '#3a3f38')
  rect(ctx, bx, by, 1, 8, '#3a3f38')
  rect(ctx, bx + 7, by, 1, 8, '#3a3f38')
  rect(ctx, bx + 3, by + 8, 2, 1, '#3a3f38')
  const ink = kind === 'block' ? '#a9352b' : '#8a5a12'
  rect(ctx, bx + 3, by + 2, 2, 3, ink)
  rect(ctx, bx + 3, by + 6, 2, 1, ink)
}

export function drawDesks(ctx: Ctx, agents: Agent[], lights: Record<string, number>) {
  for (const a of agents) {
    const x = a.desk_x
    const y = a.desk_y

    ctx.fillStyle = C.shadow
    ctx.fillRect(x + 1, y + DESK.h - 1, DESK.w, 2)

    rect(ctx, x, y, DESK.w, DESK.h, C.deskEdge)
    rect(ctx, x, y, DESK.w, DESK.h - 2, C.deskTop)
    rect(ctx, x, y + DESK.h - 2, DESK.w, 2, C.desk)

    // monitor
    const mx = x + 8
    const my = y - 1
    rect(ctx, mx, my, 8, 6, C.monitor)
    const glow = lights[a.id] ?? 0
    if (glow > 0) {
      rect(ctx, mx + 1, my + 1, 6, 4, C.screen)
      ctx.fillStyle = `rgba(255,255,255,${0.18 * glow})`
      for (let i = 0; i < 3; i++) ctx.fillRect(mx + 2, my + 2 + i, 5 - i, 1)
    } else {
      rect(ctx, mx + 1, my + 1, 6, 4, '#171b1e')
    }
    rect(ctx, mx + 3, my + 6, 2, 2, C.monitor)

    // paper and cup
    rect(ctx, x + 18, y + 3, 4, 3, '#efeade')
    rect(ctx, x + 3, y + 3, 2, 2, a.palette.trim)
  }
}
