'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
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
    <div className="h-72 w-full p-4 md:h-80 font-mono">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 16, right: 8, left: 8, bottom: 4 }}>
          <defs>
            <linearGradient id="colorPat" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00f3ff" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#00f3ff" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis
            dataKey="month"
            tick={{ fill: 'rgba(0, 243, 255, 0.4)', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: 'rgba(0, 243, 255, 0.4)', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              borderRadius: '0',
              border: '1px solid rgba(0, 243, 255, 0.3)',
              background: 'rgba(0, 0, 0, 0.9)',
              color: '#00f3ff',
              fontSize: '10px',
              fontFamily: 'monospace'
            }}
            itemStyle={{ color: '#00f3ff' }}
          />
          <Area
            type="monotone"
            dataKey="patrimonio"
            stroke="#00f3ff"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorPat)"
            animationDuration={2000}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
