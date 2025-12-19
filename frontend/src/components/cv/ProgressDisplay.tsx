import { Progress } from '@/components/ui/progress';
import { Card } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

interface ProgressDisplayProps {
  progress: number;
  currentStep: string;
}

export function ProgressDisplay({ progress, currentStep }: ProgressDisplayProps) {
  return (
    <Card className="p-6 bg-muted/50 animate-fade-in">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-primary animate-spin" />
          <h3 className="font-display font-semibold">Analysis Progress</h3>
        </div>
        
        <Progress value={progress} className="h-2" />
        
        <div className="flex items-center justify-between text-sm">
          <p className="text-muted-foreground">
            📊 {currentStep || 'Processing...'}
          </p>
          <span className="font-medium text-primary">{Math.round(progress)}%</span>
        </div>
      </div>
    </Card>
  );
}