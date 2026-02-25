'use client';

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export type WealthCurvePoint = {
  month: string;
  patrimonio: number;
};

type WealthCurveChartProps = {
  data: WealthCurvePoint[];
};

export function WealthCurveChart({ data }: WealthCurveChartProps) {
  return (
    <div className="rounded-2xl border border-neutralDark-300 bg-gradient-to-b from-neutralDark-100 via-neutralDark-200 to-neutralDark-100 p-4">
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 12, right: 12, left: 2, bottom: 2 }}>
            <CartesianGrid stroke="rgba(255,255,255,0.1)" strokeDasharray="3 3" />
            <XAxis dataKey="month" stroke="#a3a3a3" tickLine={false} axisLine={false} />
            <YAxis stroke="#a3a3a3" tickLine={false} axisLine={false} width={48} />
            <Tooltip
              contentStyle={{
                borderRadius: '12px',
                border: '1px solid #171717',
                backgroundColor: 'rgba(17,17,17,0.95)',
                color: '#f5f5f5',
              }}
              cursor={{ stroke: '#3A82F7', opacity: 0.35 }}
            />
            <Line
              type="monotone"
              dataKey="patrimonio"
              stroke="#3A82F7"
              strokeWidth={2.2}
              dot={false}
              activeDot={{ r: 4, fill: '#F59E0B', strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
