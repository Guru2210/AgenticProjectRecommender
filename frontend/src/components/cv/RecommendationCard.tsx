import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Github, Youtube, Folder, ExternalLink, Star, Clock, AlertCircle, BookOpen } from 'lucide-react';
import { SkillGapRecommendation } from '@/types/analysis';
import { AnimatedProgressBar } from './charts/AnimatedProgressBar';
import ReactMarkdown from 'react-markdown';

interface RecommendationCardProps {
  recommendation: SkillGapRecommendation;
  index: number;
}

export function RecommendationCard({ recommendation, index }: RecommendationCardProps) {
  const { skill_gap, recommended_projects, github_resources, youtube_resources, web_resources, learning_path } = recommendation;

  const priorityColors: Record<string, { bg: string; border: string; text: string; accent: string }> = {
    high: { bg: 'bg-destructive/5', border: 'border-l-destructive', text: 'text-destructive', accent: 'bg-destructive/10' },
    required: { bg: 'bg-destructive/5', border: 'border-l-destructive', text: 'text-destructive', accent: 'bg-destructive/10' },
    medium: { bg: 'bg-warning/5', border: 'border-l-warning', text: 'text-warning', accent: 'bg-warning/10' },
    preferred: { bg: 'bg-warning/5', border: 'border-l-warning', text: 'text-warning', accent: 'bg-warning/10' },
    low: { bg: 'bg-success/5', border: 'border-l-success', text: 'text-success', accent: 'bg-success/10' },
    optional: { bg: 'bg-success/5', border: 'border-l-success', text: 'text-success', accent: 'bg-success/10' },
  };

  const priorityKey = skill_gap.priority.toLowerCase();
  const colors = priorityColors[priorityKey] || priorityColors.medium;

  const totalResources = (recommended_projects?.length || 0) + (github_resources?.length || 0) + (youtube_resources?.length || 0) + (web_resources?.length || 0);

  return (
    <Accordion type="single" collapsible defaultValue={index <= 2 ? `item-${index}` : undefined}>
      <AccordionItem
        value={`item-${index}`}
        className={`border rounded-lg border-l-4 ${colors.border} ${colors.bg} transition-all hover:shadow-md`}
      >
        <AccordionTrigger className="hover:no-underline py-4 px-4">
          <div className="flex items-center gap-3 text-left w-full">
            <span className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold shrink-0">
              {index + 1}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-display font-semibold">{skill_gap.skill_name}</span>
                <Badge variant="outline" className={`${colors.accent} ${colors.text} border-transparent`}>
                  {skill_gap.priority}
                </Badge>
              </div>
              <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Folder className="w-3 h-3" />
                  {recommended_projects?.length || 0} projects
                </span>
                <span className="flex items-center gap-1">
                  <Github className="w-3 h-3" />
                  {github_resources?.length || 0} repos
                </span>
                <span className="flex items-center gap-1">
                  <Youtube className="w-3 h-3" />
                  {youtube_resources?.length || 0} videos
                </span>
                <span className="flex items-center gap-1">
                  <ExternalLink className="w-3 h-3" />
                  {web_resources?.length || 0} links
                </span>
              </div>
            </div>
          </div>
        </AccordionTrigger>

        <AccordionContent className="pb-4 px-4">
          <div className="space-y-6 pt-2">
            {/* Skill Gap Info */}
            <div className="p-4 bg-muted/50 rounded-lg space-y-3">
              {skill_gap.category && (
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Category</p>
                  <Badge variant="secondary">{skill_gap.category}</Badge>
                </div>
              )}
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Impact</p>
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-warning mt-0.5 shrink-0" />
                  <p className="text-sm text-muted-foreground">{skill_gap.impact}</p>
                </div>
              </div>
            </div>

            {/* Learning Path */}
            {learning_path && (
              <Card className="p-4 bg-primary/5 border-primary/20">
                <h5 className="font-medium mb-2 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-primary" />
                  Suggested Learning Path
                </h5>
                <div className="text-sm text-muted-foreground prose prose-sm max-w-none">
                  <ReactMarkdown
                    components={{
                      h1: ({ node, ...props }) => <h1 className="text-base font-semibold mt-3 mb-2" {...props} />,
                      h2: ({ node, ...props }) => <h2 className="text-base font-semibold mt-3 mb-2" {...props} />,
                      h3: ({ node, ...props }) => <h3 className="text-sm font-semibold mt-2 mb-1" {...props} />,
                      p: ({ node, ...props }) => <p className="mb-2 leading-relaxed" {...props} />,
                      ul: ({ node, ...props }) => <ul className="list-disc ml-5 mb-2 space-y-1" {...props} />,
                      ol: ({ node, ...props }) => <ol className="list-decimal ml-5 mb-2 space-y-1" {...props} />,
                      li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                      strong: ({ node, ...props }) => <strong className="font-semibold text-foreground" {...props} />,
                      a: ({ node, ...props }) => <a className="text-primary hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                    }}
                  >
                    {learning_path}
                  </ReactMarkdown>
                </div>
              </Card>
            )}

            {/* Projects */}
            {recommended_projects?.length > 0 && (
              <div className="space-y-3">
                <h5 className="font-medium flex items-center gap-2">
                  <Folder className="w-4 h-4 text-primary" />
                  Recommended Projects ({recommended_projects.length})
                </h5>
                <div className="grid gap-3">
                  {recommended_projects.map((project, idx) => (
                    <Card key={idx} className="p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h6 className="font-medium">{project.title}</h6>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground shrink-0">
                          <Badge variant="secondary" className="text-xs">
                            {project.difficulty}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">{project.description}</p>

                      {/* Estimated Hours Progress */}
                      {project.estimated_hours && (
                        <div className="mb-3">
                          <AnimatedProgressBar
                            value={0}
                            max={project.estimated_hours}
                            label="Estimated Time"
                            variant="default"
                            showPercentage={false}
                            className="mb-0"
                          />
                        </div>
                      )}

                      {/* Skills Covered */}
                      {project.skills_covered?.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-muted-foreground mb-1.5">Skills Covered:</p>
                          <div className="flex flex-wrap gap-1.5">
                            {project.skills_covered.map((skill, i) => (
                              <Badge key={i} variant="outline" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Learning Outcomes */}
                      {project.learning_outcomes?.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-muted-foreground mb-1.5">Learning Outcomes:</p>
                          <ul className="text-xs text-muted-foreground space-y-1">
                            {project.learning_outcomes.map((outcome, i) => (
                              <li key={i} className="flex items-start gap-1.5">
                                <span className="text-primary mt-0.5">•</span>
                                <span>{outcome}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Key Features */}
                      {project.key_features?.length > 0 && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-1.5">Key Features:</p>
                          <ul className="text-xs text-muted-foreground space-y-1">
                            {project.key_features.map((feature, i) => (
                              <li key={i} className="flex items-start gap-1.5">
                                <span className="text-primary mt-0.5">•</span>
                                <span>{feature}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* GitHub Resources */}
            {github_resources?.length > 0 && (
              <div className="space-y-3">
                <h5 className="font-medium flex items-center gap-2">
                  <Github className="w-4 h-4" />
                  GitHub Resources ({github_resources.length})
                </h5>
                <div className="grid sm:grid-cols-2 gap-3">
                  {github_resources.map((resource, idx) => (
                    <a
                      key={idx}
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group p-3 border rounded-lg hover:border-primary/50 hover:bg-accent/30 transition-all hover:shadow-md"
                    >
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <span className="font-medium text-sm group-hover:text-primary transition-colors">
                          {resource.title}
                        </span>
                        <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                      </div>
                      {resource.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                          {resource.description}
                        </p>
                      )}
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        {resource.stars !== undefined && (
                          <span className="flex items-center gap-1">
                            <Star className="w-3 h-3 text-warning fill-warning" />
                            {resource.stars.toLocaleString()}
                          </span>
                        )}
                        {resource.language && (
                          <Badge variant="outline" className="text-xs h-5">
                            {resource.language}
                          </Badge>
                        )}
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* YouTube Resources */}
            {youtube_resources?.length > 0 && (
              <div className="space-y-3">
                <h5 className="font-medium flex items-center gap-2">
                  <Youtube className="w-4 h-4 text-destructive" />
                  YouTube Tutorials ({youtube_resources.length})
                </h5>
                <div className="grid sm:grid-cols-2 gap-3">
                  {youtube_resources.map((resource, idx) => (
                    <a
                      key={idx}
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group p-3 border rounded-lg hover:border-destructive/50 hover:bg-accent/30 transition-all hover:shadow-md"
                    >
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <span className="font-medium text-sm group-hover:text-destructive transition-colors line-clamp-2">
                          {resource.title}
                        </span>
                        <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                        {resource.channel && <span>{resource.channel}</span>}
                        {resource.duration && (
                          <>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {resource.duration}
                            </span>
                          </>
                        )}
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Web Resources */}
            {web_resources?.length > 0 && (
              <div className="space-y-3">
                <h5 className="font-medium flex items-center gap-2">
                  <ExternalLink className="w-4 h-4 text-primary" />
                  Web Resources ({web_resources.length})
                </h5>
                <div className="grid sm:grid-cols-2 gap-3">
                  {web_resources.map((resource, idx) => (
                    <a
                      key={idx}
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group p-3 border rounded-lg hover:border-primary/50 hover:bg-accent/30 transition-all hover:shadow-md"
                    >
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <span className="font-medium text-sm group-hover:text-primary transition-colors line-clamp-2">
                          {resource.title}
                        </span>
                        <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                      </div>
                      {resource.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                          {resource.description}
                        </p>
                      )}
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="truncate">{new URL(resource.url).hostname.replace('www.', '')}</span>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}