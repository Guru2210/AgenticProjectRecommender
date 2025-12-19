import { useState, useCallback } from 'react';
import { AnalysisResult, JobStatus, ApiConfig } from '@/types/analysis';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export function useAnalysis() {
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [apiConfig, setApiConfig] = useState<ApiConfig | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/health`, { 
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      const healthy = response.ok;
      setBackendHealthy(healthy);
      
      // Mock API config for now - in real implementation, get from backend
      setApiConfig({
        openai: true,
        github: true,
        youtube: true
      });
      
      return healthy;
    } catch {
      setBackendHealthy(false);
      return false;
    }
  }, []);

  const pollStatus = useCallback(async (jobId: string): Promise<JobStatus | null> => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/status/${jobId}`);
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch {
      return null;
    }
  }, []);

  const getResults = useCallback(async (jobId: string): Promise<AnalysisResult | null> => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/results/${jobId}`);
      if (response.ok) {
        const data = await response.json();
        return data.result;
      }
      return null;
    } catch {
      return null;
    }
  }, []);

  const submitAnalysis = useCallback(async (cvFile: File, jobDescription: string) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setProgress(0);
    setCurrentStep('Submitting analysis...');

    try {
      const formData = new FormData();
      formData.append('cv_file', cvFile);
      formData.append('job_description', jobDescription);

      const response = await fetch(`${BACKEND_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit analysis');
      }

      const { job_id } = await response.json();
      
      // Poll for status
      let attempts = 0;
      const maxAttempts = 300;

      while (attempts < maxAttempts) {
        const status = await pollStatus(job_id);
        
        if (!status) {
          throw new Error('Failed to get job status');
        }

        setProgress(status.progress_percentage);
        setCurrentStep(status.current_step);

        if (status.status === 'completed') {
          const analysisResult = await getResults(job_id);
          if (analysisResult) {
            setResult(analysisResult);
            setIsLoading(false);
            return analysisResult;
          }
          throw new Error('Failed to get results');
        }

        if (status.status === 'failed') {
          throw new Error(status.error || 'Analysis failed');
        }

        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;
      }

      throw new Error('Analysis timed out');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(message);
      setIsLoading(false);
      return null;
    }
  }, [pollStatus, getResults]);

  const reset = useCallback(() => {
    setIsLoading(false);
    setProgress(0);
    setCurrentStep('');
    setResult(null);
    setError(null);
  }, []);

  return {
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
  };
}