import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface AnimatedProgressBarProps {
    value: number;
    max: number;
    label: string;
    variant?: 'success' | 'warning' | 'destructive' | 'default';
    showPercentage?: boolean;
    className?: string;
}

export function AnimatedProgressBar({
    value,
    max,
    label,
    variant = 'default',
    showPercentage = true,
    className
}: AnimatedProgressBarProps) {
    const percentage = max > 0 ? (value / max) * 100 : 0;

    const variantColors = {
        success: 'text-success',
        warning: 'text-warning',
        destructive: 'text-destructive',
        default: 'text-primary',
    };

    return (
        <div className={cn('space-y-2', className)}>
            <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{label}</span>
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">{value}/{max}</span>
                    {showPercentage && (
                        <span className={cn('font-semibold', variantColors[variant])}>
                            {percentage.toFixed(0)}%
                        </span>
                    )}
                </div>
            </div>
            <Progress
                value={percentage}
                className={cn(
                    'h-2 transition-all duration-1000 ease-out',
                    variant === 'success' && '[&>div]:bg-success',
                    variant === 'warning' && '[&>div]:bg-warning',
                    variant === 'destructive' && '[&>div]:bg-destructive',
                )}
            />
        </div>
    );
}
