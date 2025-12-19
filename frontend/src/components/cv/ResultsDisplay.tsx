import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Download, Clock, CheckCircle, Target, Folder, Github, Youtube } from 'lucide-react';
import { AnalysisResult } from '@/types/analysis';
import { SkillMatchDisplay } from './SkillMatchDisplay';
import { RecommendationCard } from './RecommendationCard';
import { PriorityDistributionChart } from './charts/PriorityDistributionChart';
import ReactMarkdown from 'react-markdown';

interface ResultsDisplayProps {
  result: AnalysisResult;
}

export function ResultsDisplay({ result }: ResultsDisplayProps) {
  console.log('ResultsDisplay received result:', result);
  console.log('skill_match_analysis:', result?.skill_match_analysis);
  console.log('skill_gap_recommendations:', result?.skill_gap_recommendations);

  const handleExport = () => {
    const jsonData = JSON.stringify(result, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cv_analysis_results.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Calculate statistics
  const totalProjects = result.skill_gap_recommendations?.reduce((sum, rec) => sum + (rec.recommended_projects?.length || 0), 0) || 0;
  const totalGithubRepos = result.skill_gap_recommendations?.reduce((sum, rec) => sum + (rec.github_resources?.length || 0), 0) || 0;
  const totalYoutubeVideos = result.skill_gap_recommendations?.reduce((sum, rec) => sum + (rec.youtube_resources?.length || 0), 0) || 0;

  // Calculate priority distribution
  const priorityCount = result.skill_gap_recommendations?.reduce((acc, rec) => {
    const priority = rec.skill_gap.priority.toLowerCase();
    if (priority.includes('high') || priority.includes('required')) acc.high++;
    else if (priority.includes('medium') || priority.includes('preferred')) acc.medium++;
    else acc.low++;
    return acc;
  }, { high: 0, medium: 0, low: 0 }) || { high: 0, medium: 0, low: 0 };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Success Message */}
      <div className="flex items-center gap-3 p-4 bg-success/10 border border-success/20 rounded-lg">
        <CheckCircle className="w-6 h-6 text-success" />
        <span className="font-medium text-success">Analysis complete!</span>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={<Target className="w-5 h-5 text-primary" />}
          label="Skill Gaps"
          value={result.skill_gap_recommendations?.length || 0}
          color="primary"
        />
        <StatCard
          icon={<Folder className="w-5 h-5 text-success" />}
          label="Projects"
          value={totalProjects}
          color="success"
        />
        <StatCard
          icon={<Github className="w-5 h-5 text-foreground" />}
          label="GitHub Repos"
          value={totalGithubRepos}
          color="default"
        />
        <StatCard
          icon={<Youtube className="w-5 h-5 text-destructive" />}
          label="YouTube Videos"
          value={totalYoutubeVideos}
          color="destructive"
        />
      </div>

      {/* Skill Match Analysis */}
      {result.skill_match_analysis && (
        <SkillMatchDisplay analysis={result.skill_match_analysis} />
      )}

      <Separator />

      {/* Overall Assessment and Priority Distribution */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Overall Assessment */}
        <Card className="p-6 md:col-span-2">
          <h3 className="text-lg font-display font-semibold mb-4">📝 Overall Assessment</h3>
          <div className="prose prose-sm max-w-none text-muted-foreground">
            <ReactMarkdown
              components={{
                h1: ({ node, ...props }) => <h1 className="text-base font-semibold mt-3 mb-2 text-foreground" {...props} />,
                h2: ({ node, ...props }) => <h2 className="text-base font-semibold mt-3 mb-2 text-foreground" {...props} />,
                h3: ({ node, ...props }) => <h3 className="text-sm font-semibold mt-2 mb-1 text-foreground" {...props} />,
                p: ({ node, ...props }) => <p className="mb-2 leading-relaxed" {...props} />,
                ul: ({ node, ...props }) => <ul className="list-disc ml-5 mb-2 space-y-1" {...props} />,
                ol: ({ node, ...props }) => <ol className="list-decimal ml-5 mb-2 space-y-1" {...props} />,
                li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                strong: ({ node, ...props }) => <strong className="font-semibold text-foreground" {...props} />,
              }}
            >
              {result.overall_assessment || 'No assessment available'}
            </ReactMarkdown>
          </div>

          {result.estimated_preparation_time && (
            <div className="flex items-center gap-2 mt-4 p-3 bg-accent rounded-lg">
              <Clock className="w-5 h-5 text-primary" />
              <span className="text-sm">
                <strong>Estimated Preparation Time:</strong> {result.estimated_preparation_time}
              </span>
            </div>
          )}
        </Card>

        {/* Priority Distribution */}
        {(priorityCount.high > 0 || priorityCount.medium > 0 || priorityCount.low > 0) && (
          <PriorityDistributionChart priorities={priorityCount} />
        )}
      </div>

      <Separator />

      {/* Skill Gap Recommendations */}
      <div className="space-y-4">
        <h3 className="text-lg font-display font-semibold">💡 Skill Gap Recommendations</h3>

        {result.skill_gap_recommendations?.length > 0 ? (
          <div className="space-y-3">
            {result.skill_gap_recommendations.map((rec, idx) => (
              <RecommendationCard key={idx} recommendation={rec} index={idx} />
            ))}
          </div>
        ) : (
          <Card className="p-6 text-center bg-success/5 border-success/20">
            <CheckCircle className="w-12 h-12 text-success mx-auto mb-3" />
            <h4 className="font-display font-semibold text-success">No skill gaps identified!</h4>
            <p className="text-sm text-muted-foreground mt-1">
              You're well-qualified for this role.
            </p>
          </Card>
        )}
      </div>

      <Separator />

      {/* Export */}
      <Card className="p-6">
        <h3 className="text-lg font-display font-semibold mb-4">📥 Export Results</h3>
        <div className="flex flex-col sm:flex-row gap-4">
          <Button onClick={handleExport} variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            Download as JSON
          </Button>
          <p className="text-sm text-muted-foreground self-center">
            💡 Save these recommendations for your learning journey!
          </p>
        </div>
      </Card>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'primary' | 'success' | 'destructive' | 'default';
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  const colorClasses = {
    primary: 'bg-primary/10 border-primary/20',
    success: 'bg-success/10 border-success/20',
    destructive: 'bg-destructive/10 border-destructive/20',
    default: 'bg-muted border-border',
  };

  return (
    <Card className={`p-4 ${colorClasses[color]}`}>
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-background/50">
          {icon}
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-xs text-muted-foreground">{label}</p>
        </div>
      </div>
    </Card>
  );
}