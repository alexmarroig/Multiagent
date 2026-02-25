'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

type WealthPoint = {
  month: string;
  patrimonio: number;
};

type WealthCurveChartProps = {
  data: WealthPoint[];
};

export function WealthCurveChart({ data }: WealthCurveChartProps) {
  return (
    <div className="h-72 w-full rounded-2xl border border-neutralDark-300 bg-gradient-to-b from-neutralDark-100 via-neutralDark-200 to-neutralDark-100 p-4 md:h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 16, right: 8, left: 8, bottom: 4 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.1)" strokeDasharray="3 3" opacity={0.1} />
          <XAxis dataKey="month" tick={{ fill: '#A3A3A3', fontSize: 12 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#A3A3A3', fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              borderRadius: '0.75rem',
              border: '1px solid #171717',
              background: 'rgba(17,17,17,0.95)',
              color: '#f5f5f5',
            }}
            labelStyle={{ color: '#d4d4d4' }}
          />
          <Line type="monotone" dataKey="patrimonio" stroke="#3A82F7" strokeWidth={2.2} dot={false} activeDot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
