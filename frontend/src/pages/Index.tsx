import { useState, useEffect } from 'react';
import { Rocket, Upload, BookOpen, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Sidebar } from '@/components/cv/Sidebar';
import { FileUpload } from '@/components/cv/FileUpload';
import { JobDescriptionInput } from '@/components/cv/JobDescriptionInput';
import { ProgressDisplay } from '@/components/cv/ProgressDisplay';
import { ResultsDisplay } from '@/components/cv/ResultsDisplay';
import { InstructionsTab } from '@/components/cv/InstructionsTab';
import { useAnalysis } from '@/hooks/useAnalysis';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const Index = () => {
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  
  const {
    isLoading,
    progress,
    currentStep,
    result,
    error,
    backendHealthy,
    apiConfig,
    checkHealth,
    submitAnalysis,
    reset,
  } = useAnalysis();

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  const handleAnalyze = async () => {
    if (!cvFile || jobDescription.length < 50) return;
    await submitAnalysis(cvFile, jobDescription);
  };

  const canAnalyze = cvFile && jobDescription.length >= 50 && !isLoading && backendHealthy;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl font-display font-bold gradient-text mb-2">
              🎯 CV Project Recommender
            </h1>
            <p className="text-muted-foreground text-lg">
              AI-powered skill gap analysis and project recommendations
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="flex gap-8">
          {/* Sidebar */}
          <Sidebar 
            backendHealthy={backendHealthy} 
            apiConfig={apiConfig}
            backendUrl={BACKEND_URL}
          />

          {/* Main Area */}
          <main className="flex-1 min-w-0">
            <Tabs defaultValue="upload" className="space-y-6">
              <TabsList className="grid w-full max-w-md grid-cols-2">
                <TabsTrigger value="upload" className="gap-2">
                  <Upload className="w-4 h-4" />
                  Upload & Analyze
                </TabsTrigger>
                <TabsTrigger value="instructions" className="gap-2">
                  <BookOpen className="w-4 h-4" />
                  Instructions
                </TabsTrigger>
              </TabsList>

              <TabsContent value="upload" className="space-y-8">
                {/* Backend Warning */}
                {backendHealthy === false && (
                  <Alert variant="destructive">
                    <AlertTriangle className="w-4 h-4" />
                    <AlertDescription>
                      Backend is not available. Please start the backend server first:
                      <code className="block mt-2 text-xs bg-background/50 p-2 rounded">
                        uvicorn backend.main:app --reload --port 8000
                      </code>
                    </AlertDescription>
                  </Alert>
                )}

                {/* Error Display */}
                {error && (
                  <Alert variant="destructive">
                    <AlertTriangle className="w-4 h-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {/* Results */}
                {result ? (
                  <div className="space-y-6">
                    <Button variant="outline" onClick={reset}>
                      ← Start New Analysis
                    </Button>
                    <ResultsDisplay result={result} />
                  </div>
                ) : (
                  <>
                    {/* File Upload */}
                    <FileUpload file={cvFile} onFileChange={setCvFile} />

                    <Separator />

                    {/* Job Description */}
                    <JobDescriptionInput 
                      value={jobDescription} 
                      onChange={setJobDescription} 
                    />

                    <Separator />

                    {/* Progress */}
                    {isLoading && (
                      <ProgressDisplay progress={progress} currentStep={currentStep} />
                    )}

                    {/* Analyze Button */}
                    <div className="flex justify-center pt-4">
                      <Button
                        size="lg"
                        className="gap-2 px-8 py-6 text-lg gradient-bg hover:opacity-90 transition-opacity"
                        onClick={handleAnalyze}
                        disabled={!canAnalyze}
                      >
                        <Rocket className="w-5 h-5" />
                        Analyze & Generate Recommendations
                      </Button>
                    </div>
                  </>
                )}
              </TabsContent>

              <TabsContent value="instructions">
                <InstructionsTab />
              </TabsContent>
            </Tabs>
          </main>
        </div>
      </div>
    </div>
  );
};

export default Index;