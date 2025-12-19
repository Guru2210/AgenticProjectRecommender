import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Card } from '@/components/ui/card';

interface SkillDistributionChartProps {
    matched: number;
    missingRequired: number;
    missingPreferred: number;
}

export function SkillDistributionChart({ matched, missingRequired, missingPreferred }: SkillDistributionChartProps) {
    const data = [
        { name: 'Matched Skills', value: matched, color: 'hsl(var(--success))' },
        { name: 'Missing Required', value: missingRequired, color: 'hsl(var(--destructive))' },
        { name: 'Missing Preferred', value: missingPreferred, color: 'hsl(var(--warning))' },
    ].filter(item => item.value > 0);

    if (data.length === 0) return null;

    return (
        <Card className="p-4">
            <h4 className="text-sm font-medium mb-4 text-center">Skill Distribution</h4>
            <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={2}
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
                    />
                    <Legend
                        verticalAlign="bottom"
                        height={36}
                        iconType="circle"
                        formatter={(value) => <span className="text-xs">{value}</span>}
                    />
                </PieChart>
            </ResponsiveContainer>
        </Card>
    );
}
