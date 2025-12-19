import { useCallback, useState } from 'react';
import { Upload, FileText, X, Lightbulb } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface FileUploadProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
}

export function FileUpload({ file, onFileChange }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.type === 'application/pdf' || 
        droppedFile.name.endsWith('.docx'))) {
      onFileChange(droppedFile);
    }
  }, [onFileChange]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      onFileChange(selectedFile);
    }
  }, [onFileChange]);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-display font-semibold flex items-center gap-2">
        <span className="w-8 h-8 rounded-full gradient-bg flex items-center justify-center text-primary-foreground text-sm font-bold">1</span>
        Upload Your CV
      </h2>
      
      <div className="grid md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <label
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={cn(
              "flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200",
              isDragging 
                ? "border-primary bg-accent/50" 
                : "border-border hover:border-primary/50 hover:bg-accent/30",
              file && "border-success bg-success/5"
            )}
          >
            <input
              type="file"
              className="hidden"
              accept=".pdf,.docx"
              onChange={handleFileInput}
            />
            
            {file ? (
              <div className="flex items-center gap-3 px-4">
                <div className="w-12 h-12 rounded-lg bg-success/10 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-success" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="shrink-0"
                  onClick={(e) => {
                    e.preventDefault();
                    onFileChange(null);
                  }}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-muted-foreground">
                <Upload className="w-10 h-10" />
                <p className="text-sm font-medium">
                  <span className="text-primary">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs">PDF or DOCX (max 10MB)</p>
              </div>
            )}
          </label>
        </div>
        
        <Card className="p-4 bg-accent/50 border-accent">
          <div className="flex items-start gap-2">
            <Lightbulb className="w-5 h-5 text-primary shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-sm text-accent-foreground">Tip</p>
              <p className="text-xs text-muted-foreground mt-1">
                Make sure your CV includes:
              </p>
              <ul className="text-xs text-muted-foreground mt-1 space-y-0.5">
                <li>• Skills</li>
                <li>• Work experience</li>
                <li>• Education</li>
                <li>• Certifications</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}