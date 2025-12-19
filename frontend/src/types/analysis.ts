// Updated types to match backend Pydantic models

export interface SkillMatchAnalysis {
  total_required_skills: number;
  matched_skills: string[];
  missing_required_skills: string[];
  missing_preferred_skills: string[];
  match_percentage: number;
  strengths: string[];
  areas_for_improvement: string[];
}

export interface SkillGap {
  skill_name: string;
  priority: string;
  category?: string;
  impact: string;
}

export interface Project {
  title: string;
  description: string;
  skills_covered: string[];
  difficulty: string;
  estimated_hours?: number;
  key_features: string[];
  learning_outcomes: string[];
}

export interface Resource {
  type: string;
  title: string;
  url: string;
  description?: string;
  // GitHub-specific fields
  stars?: number;
  language?: string;
  last_updated?: string;
  // YouTube-specific fields
  channel?: string;
  duration?: string;
  views?: number;
  relevance_score?: number;
}

export interface SkillGapRecommendation {
  skill_gap: SkillGap;
  recommended_projects: Project[];
  github_resources: Resource[];
  youtube_resources: Resource[];
  web_resources: Resource[];
  learning_path?: string;
}

export interface AnalysisResult {
  skill_match_analysis: SkillMatchAnalysis;
  overall_assessment: string;
  estimated_preparation_time?: string;
  skill_gap_recommendations: SkillGapRecommendation[];
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  current_step: string;
  error?: string;
}

export interface ApiConfig {
  openai: boolean;
  github: boolean;
  youtube: boolean;
}