import type { ReactNode } from 'react';

export function ResponsiveContainer({ children }: { children?: ReactNode }) {
  return <>{children}</>;
}

const Empty = () => null;

export const BarChart = Empty;
export const Bar = Empty;
export const XAxis = Empty;
export const YAxis = Empty;
export const CartesianGrid = Empty;
export const Tooltip = Empty;
