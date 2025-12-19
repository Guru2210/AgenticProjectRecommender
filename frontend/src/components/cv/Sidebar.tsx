import { CheckCircle, XCircle, AlertCircle, Info, Settings, Key } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ApiConfig } from '@/types/analysis';

interface SidebarProps {
  backendHealthy: boolean | null;
  apiConfig: ApiConfig | null;
  backendUrl: string;
}

export function Sidebar({ backendHealthy, apiConfig, backendUrl }: SidebarProps) {
  return (
    <aside className="w-80 flex-shrink-0 hidden lg:block">
      <div className="sticky top-8 space-y-6">
        <Card className="p-6 glass">
          <div className="flex items-center gap-2 mb-4">
            <Info className="w-5 h-5 text-primary" />
            <h3 className="font-display font-semibold">About</h3>
          </div>
          <ul className="space-y-3 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="text-lg">📄</span>
              <span>Parse your CV automatically</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-lg">🎯</span>
              <span>Analyze job requirements</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-lg">📊</span>
              <span>Identify skill gaps</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-lg">💡</span>
              <span>Get project recommendations</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-lg">📚</span>
              <span>Find learning resources</span>
            </li>
          </ul>
        </Card>

        <Card className="p-6 glass">
          <div className="flex items-center gap-2 mb-4">
            <Settings className="w-5 h-5 text-primary" />
            <h3 className="font-display font-semibold">Settings</h3>
          </div>
          <p className="text-xs text-muted-foreground mb-3 font-mono">
            Backend: {backendUrl}
          </p>
          
          {backendHealthy === null ? (
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="w-4 h-4 rounded-full bg-muted animate-pulse" />
              <span className="text-sm">Checking...</span>
            </div>
          ) : backendHealthy ? (
            <div className="flex items-center gap-2 text-success">
              <CheckCircle className="w-4 h-4" />
              <span className="text-sm font-medium">Backend connected</span>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-destructive">
                <XCircle className="w-4 h-4" />
                <span className="text-sm font-medium">Backend unavailable</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Make sure the backend is running:
              </p>
              <code className="block text-xs bg-muted px-2 py-1 rounded font-mono">
                uvicorn backend.main:app --reload --port 8000
              </code>
            </div>
          )}
        </Card>

        <Card className="p-6 glass">
          <div className="flex items-center gap-2 mb-4">
            <Key className="w-5 h-5 text-primary" />
            <h3 className="font-display font-semibold">API Status</h3>
          </div>
          <div className="space-y-2">
            <StatusItem 
              label="OpenAI API" 
              status={apiConfig?.openai ? 'success' : 'error'} 
            />
            <StatusItem 
              label="GitHub API" 
              status={apiConfig?.github ? 'success' : 'warning'} 
            />
            <StatusItem 
              label="YouTube API" 
              status={apiConfig?.youtube ? 'success' : 'error'} 
            />
          </div>
        </Card>
      </div>
    </aside>
  );
}

function StatusItem({ label, status }: { label: string; status: 'success' | 'warning' | 'error' }) {
  const icons = {
    success: <CheckCircle className="w-4 h-4 text-success" />,
    warning: <AlertCircle className="w-4 h-4 text-warning" />,
    error: <XCircle className="w-4 h-4 text-destructive" />,
  };

  const labels = {
    success: 'configured',
    warning: 'limited',
    error: 'not configured',
  };

  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <div className="flex items-center gap-1.5">
        {icons[status]}
        <span className={status === 'success' ? 'text-success' : status === 'warning' ? 'text-warning' : 'text-destructive'}>
          {labels[status]}
        </span>
      </div>
    </div>
  );
}