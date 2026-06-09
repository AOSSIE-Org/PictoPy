import React, { useEffect, useState, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/app/store';
import {
  markCompleted,
  previousStep,
  setIsEditing,
} from '@/features/onboardingSlice';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
  CardDescription,
} from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Progress } from '@/components/ui/progress';
import {
  ChevronDown,
  AlertCircle,
  CheckCircle2,
  Cpu,
  HardDrive,
} from 'lucide-react';
import { BACKEND_URL } from '@/config/Backend';
import { useUserPreferences } from '@/hooks/useUserPreferences';

import { AppFeatures } from '@/components/OnboardingSteps/AppFeatures';
import {
  getModelTierDescription,
  getModelTierLabel,
  getInstalledModelTiers,
  MODEL_TIERS,
  normalizeModelTier,
  type HardwareInfo,
  type HardwareResponse,
  type ModelDownloadProgressMessage,
  type ModelStatusResponse,
  type ModelTier,
} from '@/types/models';

interface AIModelSetupStepProps {
  stepIndex: number;
  totalSteps: number;
  currentStepDisplayIndex: number;
}

type ViewMode = 'recommendation' | 'downloading' | 'complete' | 'error';

export const AIModelSetupStep: React.FC<AIModelSetupStepProps> = ({
  stepIndex,
  totalSteps,
  currentStepDisplayIndex,
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const isEditing = useSelector(
    (state: RootState) => state.onboarding.isEditing,
  );
  const { updateYoloModelSize } = useUserPreferences();

  const [viewMode, setViewMode] = useState<ViewMode>('recommendation');
  const [selectedTier, setSelectedTier] = useState<ModelTier>('small');
  const [recommendedTier, setRecommendedTier] = useState<ModelTier>('small');
  const [hardwareSpecs, setHardwareSpecs] = useState<HardwareInfo | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>('');

  // Progress tracking
  const [overallPercent, setOverallPercent] = useState<number>(0);
  const [currentModel, setCurrentModel] = useState<string>('');

  const eventSourceRef = useRef<EventSource | null>(null);

  const [isCheckingStatus, setIsCheckingStatus] = useState<boolean>(true);

  // Check if models are physically present on disk
  useEffect(() => {
    const checkModelStatus = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/models/status`);
        const data: ModelStatusResponse = await res.json();

        if (data.success && data.data) {
          const models = data.data;

          const hasFacenet = models.facenet?.installed;
          const installedTiers = getInstalledModelTiers(models);

          if (hasFacenet && installedTiers.length > 0 && !isEditing) {
            setIsCheckingStatus(false);
            dispatch(markCompleted(stepIndex));
            return;
          }
        }
      } catch (err) {
        console.error('Failed to verify model status on disk:', err);
      }
      setIsCheckingStatus(false);
    };

    checkModelStatus();
  }, [dispatch, stepIndex, isEditing]);

  // Fetch hardware recommendations on mount
  useEffect(() => {
    if (viewMode === 'recommendation') {
      fetch(`${BACKEND_URL}/models/hardware`)
        .then((res) => res.json())
        .then((data: HardwareResponse) => {
          if (data.success && data.data) {
            setRecommendedTier(normalizeModelTier(data.data.recommended_tier));
            setSelectedTier(normalizeModelTier(data.data.recommended_tier));
            setHardwareSpecs(data.data);
          }
        })
        .catch((err) => {
          console.error('Failed to fetch hardware recommendation', err);
          setRecommendedTier('small');
          setSelectedTier('small');
        });
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [viewMode]);

  const handleStartDownload = async () => {
    setViewMode('downloading');
    setOverallPercent(0);
    setErrorMsg('');

    try {
      const response = await fetch(`${BACKEND_URL}/models/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: selectedTier }),
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.detail || 'Failed to start setup');
      }

      const taskId = data.task_id;

      const source = new EventSource(
        `${BACKEND_URL}/models/download/${taskId}/progress`,
      );
      eventSourceRef.current = source;

      source.onmessage = (event) => {
        try {
          const msg: ModelDownloadProgressMessage = JSON.parse(event.data);

          if (msg.status === 'downloading') {
            const percentPerModel = 100 / msg.total_models;
            const basePercent = (msg.model_index - 1) * percentPerModel;
            const currentModelPercent = (msg.percent / 100) * percentPerModel;

            setOverallPercent(
              Math.min(100, Math.round(basePercent + currentModelPercent)),
            );
            setCurrentModel(msg.model_key);
          } else if (msg.status === 'complete') {
            setOverallPercent(100);
            setViewMode('complete');
            updateYoloModelSize(selectedTier);
            source.close();
          } else if (msg.status === 'error') {
            setErrorMsg(msg.message || 'Download failed');
            setViewMode('error');
            source.close();
          }
        } catch (err) {
          console.error('Malformed SSE payload', err);
          setErrorMsg(
            'Received malformed download progress data. Please try again.',
          );
          setViewMode('error');
          source.close();
        }
      };

      source.onerror = (err) => {
        console.error('SSE Error', err);
        setErrorMsg('Connection lost during download. Please try again.');
        setViewMode('error');
        source.close();
      };
    } catch (err) {
      setErrorMsg(
        err instanceof Error ? err.message : 'Failed to connect to backend',
      );
      setViewMode('error');
    }
  };

  const handleNext = () => {
    dispatch(markCompleted(stepIndex));
  };

  const handleBack = () => {
    dispatch(setIsEditing(true));
    dispatch(previousStep());
  };

  if (isCheckingStatus) {
    return (
      <Card className="flex max-h-full w-1/2 flex-col items-center justify-center border p-4">
        <p className="text-muted-foreground text-sm">Verifying AI models...</p>
      </Card>
    );
  }

  const progressPercent = Math.round(
    ((currentStepDisplayIndex + 1) / totalSteps) * 100,
  );

  return (
    <>
      <Card className="flex max-h-full w-1/2 flex-col gap-2 border p-4">
        {/* Header */}
        <CardHeader className="p-3">
          <div className="text-muted-foreground mb-1 flex justify-between text-xs">
            <span>
              Step {currentStepDisplayIndex + 1} of {totalSteps}
            </span>
            <span>{progressPercent}%</span>
          </div>
          <Progress value={progressPercent} className="bg-muted mb-4" />

          <CardTitle className="text-xl font-semibold">
            AI Model Setup
          </CardTitle>
          <CardDescription className="mt-2 text-base">
            PictoPy runs locally and needs to download its vision models.
          </CardDescription>
        </CardHeader>

        <CardContent className="flex-1 space-y-4 p-1 px-2">
          {/* Recommendation view */}
          {viewMode === 'recommendation' && (
            <>
              {/* Hardware summary pill */}
              {hardwareSpecs && (
                <div className="flex flex-wrap justify-between">
                  <span className="bg-muted/60 text-muted-foreground inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium">
                    <HardDrive className="h-3 w-3" />
                    {hardwareSpecs.ram_gb} GB RAM
                  </span>
                  <span className="bg-muted/60 text-muted-foreground inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium">
                    <Cpu className="h-3 w-3" />
                    {hardwareSpecs.apple_silicon
                      ? hardwareSpecs.apple_silicon
                      : hardwareSpecs.gpu_names?.length
                        ? hardwareSpecs.gpu_names.join(', ')
                        : 'No dedicated GPU'}
                  </span>
                </div>
              )}

              {/* Recommended tier card */}
              <div className="bg-primary/5 flex items-start justify-between gap-4 rounded-xl border p-4">
                <div>
                  <p className="text-primary mb-1 text-xs font-semibold tracking-wide uppercase">
                    Recommended for your hardware
                  </p>
                  <p className="text-foreground text-sm font-semibold capitalize">
                    {getModelTierLabel(recommendedTier)}
                  </p>
                  <p className="text-muted-foreground mt-0.5 text-xs">
                    {getModelTierDescription(recommendedTier)}
                  </p>
                </div>
                <CheckCircle2 className="text-primary mt-0.5 h-5 w-5 shrink-0" />
              </div>

              {/* Tier selector */}
              <div className="space-y-1.5 px-1">
                <p className="text-sm font-medium">Select model tier</p>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="outline"
                      className="h-11 w-full justify-between px-4 text-sm font-normal"
                    >
                      {getModelTierLabel(selectedTier)}
                      <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent
                    className="w-96 max-w-[calc(100vw-2rem)] min-w-80"
                    align="start"
                  >
                    <DropdownMenuRadioGroup
                      value={selectedTier}
                      onValueChange={(value) =>
                        setSelectedTier(normalizeModelTier(value))
                      }
                    >
                      {MODEL_TIERS.map((tier) => (
                        <DropdownMenuRadioItem
                          key={tier}
                          value={tier}
                          className="py-2.5"
                        >
                          <div>
                            <p className="text-sm font-medium">
                              {getModelTierLabel(tier)}
                            </p>
                            <p className="text-muted-foreground mt-0.5 text-xs">
                              {getModelTierDescription(tier)}
                            </p>
                          </div>
                        </DropdownMenuRadioItem>
                      ))}
                    </DropdownMenuRadioGroup>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </>
          )}

          {/* Downloading view */}
          {viewMode === 'downloading' && (
            <div className="flex flex-col items-center justify-center space-y-4 py-6">
              <div className="w-full space-y-2 px-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">
                    Downloading {currentModel || 'models'}…
                  </span>
                  <span className="text-muted-foreground tabular-nums">
                    {overallPercent}%
                  </span>
                </div>
                <Progress value={overallPercent} className="bg-muted" />
              </div>
              <p className="text-muted-foreground text-center text-xs">
                Please do not close the application while models are
                downloading.
              </p>
            </div>
          )}

          {/* Error view */}
          {viewMode === 'error' && (
            <div className="flex flex-col items-center justify-center space-y-3 py-6 text-center">
              <div className="bg-destructive/10 rounded-full p-4">
                <AlertCircle className="text-destructive h-8 w-8" />
              </div>
              <div>
                <p className="text-sm font-semibold">Download failed</p>
                <p className="text-muted-foreground mt-1 max-w-xs text-xs">
                  {errorMsg}
                </p>
              </div>
              <Button
                onClick={() => setViewMode('recommendation')}
                variant="outline"
                size="sm"
              >
                Try Again
              </Button>
            </div>
          )}

          {/* Complete view */}
          {viewMode === 'complete' && (
            <div className="flex flex-col items-center justify-center space-y-3 py-6 text-center">
              <div className="rounded-full bg-green-500/10 p-4">
                <CheckCircle2 className="h-8 w-8 text-green-500" />
              </div>
              <div>
                <h3 className="text-base font-semibold">Setup Complete!</h3>
                <p className="text-muted-foreground mt-1 text-sm">
                  All required models have been successfully downloaded.
                </p>
              </div>
            </div>
          )}
        </CardContent>

        {/* Footer */}
        <CardFooter className="flex justify-between p-3">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={viewMode === 'downloading'}
            className={`cursor-pointer px-4 py-1 text-sm ${viewMode === 'downloading' ? 'invisible' : ''}`}
          >
            Back
          </Button>

          {viewMode === 'recommendation' && (
            <Button
              onClick={handleStartDownload}
              className="cursor-pointer px-4 py-1 text-sm"
            >
              Download
            </Button>
          )}

          {(viewMode === 'complete' || viewMode === 'error') && (
            <Button
              onClick={handleNext}
              disabled={viewMode === 'error'}
              className="cursor-pointer px-4 py-1 text-sm"
            >
              Get Started
            </Button>
          )}
        </CardFooter>
      </Card>

      <AppFeatures />
    </>
  );
};
