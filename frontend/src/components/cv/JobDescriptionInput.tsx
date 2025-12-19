import { Textarea } from '@/components/ui/textarea';

interface JobDescriptionInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function JobDescriptionInput({ value, onChange }: JobDescriptionInputProps) {
  const charCount = value.length;
  const isValid = charCount >= 50;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-display font-semibold flex items-center gap-2">
        <span className="w-8 h-8 rounded-full gradient-bg flex items-center justify-center text-primary-foreground text-sm font-bold">2</span>
        Paste Job Description
      </h2>
      
      <div className="relative">
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Paste the complete job description here...

Include the full job posting with:
• Required skills and technologies
• Responsibilities
• Qualifications
• Nice-to-have skills"
          className="min-h-[200px] resize-none text-sm"
        />
        <div className="absolute bottom-3 right-3 text-xs text-muted-foreground">
          <span className={charCount < 50 ? 'text-destructive' : 'text-success'}>
            {charCount}
          </span>
          <span> / 50 min</span>
        </div>
      </div>
      
      {!isValid && charCount > 0 && (
        <p className="text-xs text-destructive">
          Please provide at least 50 characters for a meaningful analysis
        </p>
      )}
    </div>
  );
}