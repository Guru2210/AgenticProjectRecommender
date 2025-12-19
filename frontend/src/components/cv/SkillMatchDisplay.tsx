import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, AlertCircle, XCircle, TrendingUp, Target } from 'lucide-react';
import { SkillMatchAnalysis } from '@/types/analysis';
import { MatchPercentageGauge } from './charts/MatchPercentageGauge';
import { SkillDistributionChart } from './charts/SkillDistributionChart';
import { AnimatedProgressBar } from './charts/AnimatedProgressBar';

interface SkillMatchDisplayProps {
  analysis: SkillMatchAnalysis;
}

export function SkillMatchDisplay({ analysis }: SkillMatchDisplayProps) {
  const matchPercentage = analysis.match_percentage;
  const totalSkills = analysis.matched_skills.length + analysis.missing_required_skills.length + analysis.missing_preferred_skills.length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header with Gauge and Distribution */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Match Percentage Gauge */}
        <Card className="p-6">
          <h3 className="text-lg font-display font-semibold mb-4 text-center">Overall Match Score</h3>
          <MatchPercentageGauge percentage={matchPercentage} />
          <div className="mt-4 text-center">
            <p className="text-sm text-muted-foreground">
              {matchPercentage >= 80 ? '🎉 Excellent match!' : matchPercentage >= 60 ? '👍 Good match' : '📚 Room for improvement'}
            </p>
          </div>
        </Card>

        {/* Skill Distribution */}
        <SkillDistributionChart
          matched={analysis.matched_skills.length}
          missingRequired={analysis.missing_required_skills.length}
          missingPreferred={analysis.missing_preferred_skills.length}
        />
      </div>

      {/* Progress Bars */}
      <Card className="p-6">
        <h3 className="text-lg font-display font-semibold mb-4">📊 Skill Breakdown</h3>
        <div className="space-y-4">
          <AnimatedProgressBar
            value={analysis.matched_skills.length}
            max={totalSkills}
            label="Matched Skills"
            variant="success"
          />
          <AnimatedProgressBar
            value={analysis.missing_required_skills.length}
            max={totalSkills}
            label="Missing Required Skills"
            variant="destructive"
          />
          <AnimatedProgressBar
            value={analysis.missing_preferred_skills.length}
            max={totalSkills}
            label="Missing Preferred Skills"
            variant="warning"
          />
        </div>
      </Card>

      {/* Detailed Skills */}
      <Card className="p-6">
        <h3 className="text-lg font-display font-semibold mb-4">🔍 Detailed Analysis</h3>
        <div className="space-y-6">
          {/* Matched Skills */}
          {analysis.matched_skills.length > 0 && (
            <SkillSection
              title="Matched Skills"
              skills={analysis.matched_skills}
              icon={<CheckCircle className="w-5 h-5 text-success" />}
              badgeVariant="success"
            />
          )}

          {/* Missing Required Skills */}
          {analysis.missing_required_skills.length > 0 && (
            <SkillSection
              title="Missing Required Skills"
              skills={analysis.missing_required_skills}
              icon={<XCircle className="w-5 h-5 text-destructive" />}
              badgeVariant="destructive"
            />
          )}

          {/* Missing Preferred Skills */}
          {analysis.missing_preferred_skills.length > 0 && (
            <SkillSection
              title="Missing Preferred Skills"
              skills={analysis.missing_preferred_skills}
              icon={<AlertCircle className="w-5 h-5 text-warning" />}
              badgeVariant="warning"
            />
          )}
        </div>
      </Card>

      {/* Strengths and Areas for Improvement */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Strengths */}
        {analysis.strengths.length > 0 && (
          <Card className="p-6 bg-success/5 border-success/20">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-success" />
              <h4 className="font-display font-semibold text-success">Your Strengths</h4>
            </div>
            <ul className="space-y-2">
              {analysis.strengths.map((strength, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm">
                  <span className="text-success mt-1">✓</span>
                  <span>{strength}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {/* Areas for Improvement */}
        {analysis.areas_for_improvement.length > 0 && (
          <Card className="p-6 bg-warning/5 border-warning/20">
            <div className="flex items-center gap-2 mb-4">
              <Target className="w-5 h-5 text-warning" />
              <h4 className="font-display font-semibold text-warning">Areas for Improvement</h4>
            </div>
            <ul className="space-y-2">
              {analysis.areas_for_improvement.map((area, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm">
                  <span className="text-warning mt-1">→</span>
                  <span>{area}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </div>
  );
}

interface SkillSectionProps {
  title: string;
  skills: string[];
  icon: React.ReactNode;
  badgeVariant: 'success' | 'warning' | 'destructive';
}

function SkillSection({ title, skills, icon, badgeVariant }: SkillSectionProps) {
  if (skills.length === 0) return null;

  const variantClasses = {
    success: 'bg-success/10 text-success border-success/20',
    warning: 'bg-warning/10 text-warning border-warning/20',
    destructive: 'bg-destructive/10 text-destructive border-destructive/20',
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        {icon}
        <h4 className="font-medium">{title}</h4>
        <Badge variant="outline" className="ml-auto">
          {skills.length}
        </Badge>
      </div>

      <div className="flex flex-wrap gap-2">
        {skills.map((skill, idx) => (
          <Badge
            key={idx}
            variant="outline"
            className={variantClasses[badgeVariant]}
          >
            {skill}
          </Badge>
        ))}
      </div>
    </div>
  );
}