import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts';

interface MatchPercentageGaugeProps {
    percentage: number;
}

export function MatchPercentageGauge({ percentage }: MatchPercentageGaugeProps) {
    const getColor = (value: number) => {
        if (value >= 80) return 'hsl(var(--success))';
        if (value >= 60) return 'hsl(var(--warning))';
        return 'hsl(var(--destructive))';
    };

    const data = [
        {
            name: 'Match',
            value: percentage,
            fill: getColor(percentage),
        },
    ];

    return (
        <div className="relative">
            <ResponsiveContainer width="100%" height={260}>
                <RadialBarChart
                    cx="50%"
                    cy="50%"
                    innerRadius="90%"
                    outerRadius="250%"
                    barSize={24}
                    data={data}
                    startAngle={180}
                    endAngle={0}
                >
                    <PolarAngleAxis
                        type="number"
                        domain={[0, 100]}
                        angleAxisId={0}
                        tick={false}
                    />
                    <RadialBar
                        background
                        dataKey="value"
                        cornerRadius={10}
                        fill={getColor(percentage)}
                    />
                </RadialBarChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                    <p className={`text-6xl font-bold ${percentage >= 80 ? 'text-success' : percentage >= 60 ? 'text-warning' : 'text-destructive'}`}>
                        {percentage.toFixed(1)}%
                    </p>
                    <p className="text-sm text-muted-foreground mt-2">Match Score</p>
                </div>
            </div>
        </div>
    );
}
