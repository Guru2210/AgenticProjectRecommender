import { Card } from '@/components/ui/card';

export function InstructionsTab() {
  return (
    <div className="space-y-8 animate-fade-in">
      <Card className="p-6">
        <h2 className="text-2xl font-display font-bold mb-6">📖 How to Use</h2>
        
        <div className="space-y-6">
          <section>
            <h3 className="text-lg font-semibold mb-3">Step-by-Step Guide</h3>
            
            <div className="space-y-4">
              <Step 
                number={1}
                title="Start the Backend"
                description="Make sure the FastAPI backend is running"
                code="uvicorn backend.main:app --reload --port 8000"
              />
              
              <Step 
                number={2}
                title="Upload Your CV"
                description="Supported formats: PDF, DOCX. Ensure your CV includes skills, experience, education, and certifications"
              />
              
              <Step 
                number={3}
                title="Paste Job Description"
                description="Copy the complete job posting including requirements, responsibilities, and qualifications"
              />
              
              <Step 
                number={4}
                title="Click Analyze"
                description="The AI will process your CV and job description. This may take 30-60 seconds"
              />
              
              <Step 
                number={5}
                title="Review Results"
                description="View skill match analysis, identify gaps, get project recommendations and learning resources"
              />
            </div>
          </section>

          <section className="p-4 bg-accent/50 rounded-lg">
            <h3 className="text-lg font-semibold mb-3">✅ Tips for Best Results</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• Use a well-formatted CV with clear sections</li>
              <li>• Include specific technologies and tools in your CV</li>
              <li>• Paste the complete job description (not just a summary)</li>
              <li>• Review all recommendations, not just the first few</li>
            </ul>
          </section>

          <section className="p-4 bg-muted rounded-lg">
            <h3 className="text-lg font-semibold mb-3">⚙️ API Configuration</h3>
            <p className="text-sm text-muted-foreground mb-3">
              Configure these in your <code className="bg-background px-1.5 py-0.5 rounded">.env</code> file:
            </p>
            <ul className="space-y-2 text-sm">
              <li><strong>OPENAI_API_KEY</strong> (required) - for CV parsing and analysis</li>
              <li><strong>GITHUB_TOKEN</strong> (optional) - for better rate limits</li>
              <li><strong>YOUTUBE_API_KEY</strong> (required) - for video recommendations</li>
            </ul>
          </section>
        </div>
      </Card>
    </div>
  );
}

interface StepProps {
  number: number;
  title: string;
  description: string;
  code?: string;
}

function Step({ number, title, description, code }: StepProps) {
  return (
    <div className="flex gap-4">
      <div className="w-8 h-8 rounded-full gradient-bg flex items-center justify-center text-primary-foreground font-bold shrink-0">
        {number}
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="font-semibold">{title}</h4>
        <p className="text-sm text-muted-foreground mt-1">{description}</p>
        {code && (
          <code className="block mt-2 text-xs bg-muted p-2 rounded font-mono overflow-x-auto">
            {code}
          </code>
        )}
      </div>
    </div>
  );
}