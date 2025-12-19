import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Card } from '@/components/ui/card';

interface PriorityDistributionChartProps {
    priorities: {
        high: number;
        medium: number;
        low: number;
    };
}

export function PriorityDistributionChart({ priorities }: PriorityDistributionChartProps) {
    const data = [
        { name: 'High Priority', value: priorities.high, color: 'hsl(var(--destructive))' },
        { name: 'Medium Priority', value: priorities.medium, color: 'hsl(var(--warning))' },
        { name: 'Low Priority', value: priorities.low, color: 'hsl(var(--success))' },
    ].filter(item => item.value > 0);

    if (data.length === 0) return null;

    const total = priorities.high + priorities.medium + priorities.low;

    return (
        <Card className="p-4">
            <h4 className="text-sm font-medium mb-4 text-center">Priority Distribution</h4>
            <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={3}
                        dataKey="value"
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px',
                        }}
                        formatter={(value: number) => `${value} skill${value !== 1 ? 's' : ''}`}
                    />
                    <Legend
                        verticalAlign="bottom"
                        height={36}
                        iconType="circle"
                        formatter={(value) => <span className="text-xs">{value}</span>}
                    />
                </PieChart>
            </ResponsiveContainer>
            <div className="text-center mt-2">
                <p className="text-xs text-muted-foreground">
                    Total: {total} skill gap{total !== 1 ? 's' : ''}
                </p>
            </div>
        </Card>
    );
}
