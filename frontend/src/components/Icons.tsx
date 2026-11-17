type P = { size?: number }

const base = (size = 16) => ({
  width: size,
  height: size,
  viewBox: '0 0 16 16',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.3,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
})

export const IconOffice = ({ size }: P) => (
  <svg {...base(size)} aria-hidden="true">
    <rect x="1.5" y="2.5" width="13" height="11" />
    <path d="M1.5 6.5h13M6 6.5v7" />
  </svg>
)

export const IconOrg = ({ size }: P) => (
  <svg {...base(size)} aria-hidden="true">
    <rect x="6" y="1.5" width="4" height="3.5" />
    <rect x="1.5" y="11" width="4" height="3.5" />
    <rect x="10.5" y="11" width="4" height="3.5" />
    <path d="M8 5v3M3.5 11V8h9v3" />
  </svg>
)

export const IconThread = ({ size }: P) => (
  <svg {...base(size)} aria-hidden="true">
    <path d="M2 3.5h12v7H8l-3.5 3v-3H2z" />
  </svg>
)

export const IconLog = ({ size }: P) => (
  <svg {...base(size)} aria-hidden="true">
    <path d="M3 2.5h10v11H3zM5.5 5.5h5M5.5 8h5M5.5 10.5h3" />
  </svg>
)

export const IconMoney = ({ size }: P) => (
  <svg {...base(size)} aria-hidden="true">
    <path d="M2.5 4.5h11v7h-11zM2.5 7h11" />
    <path d="M5 10.5h2" />
  </svg>
)

export const IconShield = ({ size }: P) => (
  <svg {...base(size)} aria-hidden="true">
    <path d="M8 1.8 13 4v4.2c0 3-2.1 5.2-5 6-2.9-.8-5-3-5-6V4z" />
    <path d="m5.8 8 1.6 1.6L10.4 6.6" />
  </svg>
)

export const IconClose = ({ size = 14 }: P) => (
  <svg {...base(size)} aria-hidden="true">
    <path d="m4 4 8 8M12 4l-8 8" />
  </svg>
)

export const IconSend = ({ size = 13 }: P) => (
  <svg {...base(size)} aria-hidden="true">
    <path d="M2 8 14 2l-4 12-2.2-4.6z" />
  </svg>
)

export const IconBox = ({ size }: P) => (
  <svg {...base(size)} aria-hidden="true">
    <path d="M8 1.8 14 4.6v6.8L8 14.2 2 11.4V4.6z" />
    <path d="M2 4.6 8 7.4l6-2.8M8 7.4v6.8" />
  </svg>
)

export const IconGear = ({ size }: P) => (
  <svg {...base(size)} aria-hidden="true">
    <circle cx="8" cy="8" r="2.2" />
    <path d="M8 1.6v2M8 12.4v2M1.6 8h2M12.4 8h2M3.5 3.5l1.4 1.4M11.1 11.1l1.4 1.4M12.5 3.5l-1.4 1.4M4.9 11.1l-1.4 1.4" />
  </svg>
)
