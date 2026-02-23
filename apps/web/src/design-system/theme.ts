import { colors, spacing, typography } from './tokens';
import { shadows } from './shadows';

export const theme = {
  colors,
  spacing,
  typography,
  depth: {
    0: 'flat',
    1: `border: 1px solid ${colors.borderSubtle}`,
    2: `background: ${colors.cardElevated}; backdrop-filter: blur(16px); border: 1px solid ${colors.borderSubtle}`,
    3: `hover: translateY(-6px) with ${shadows.depth3}`,
  },
  shadows,
} as const;

export type Theme = typeof theme;
