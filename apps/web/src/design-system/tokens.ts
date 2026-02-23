export const colors = {
  backgroundPrimary: '#05070A',
  backgroundSecondary: '#0A0F1A',
  card: 'rgba(255,255,255,0.03)',
  cardElevated: 'rgba(255,255,255,0.06)',
  borderSubtle: 'rgba(255,255,255,0.08)',
  textPrimary: '#F5F7FA',
  textSecondary: '#A0AEC0',
  textTertiary: '#718096',
  accent: '#3B82F6',
  accentGlow: '#60A5FA',
} as const;

export const spacing = [4, 8, 16, 24, 32, 48, 64, 96, 128] as const;

export const typography = {
  heroTitle: 'clamp(48px, 6vw, 82px)',
  sectionTitle: '32px',
  body: '16px',
} as const;
