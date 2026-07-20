export const MODEL_TIERS = ['nano', 'small', 'medium'] as const;

export type ModelTier = (typeof MODEL_TIERS)[number];

export type ModelFeature =
  | 'object_detection'
  | 'face_detection'
  | 'face_embedding'
  | 'semantic_vision'
  | 'semantic_text';

export interface ModelEntry {
  feature: ModelFeature;
  tier: ModelTier | 'required';
  installed: boolean;
  name?: string;
  size_mb?: number;
}

export interface ModelStatusResponse {
  success: boolean;
  data: Record<string, ModelEntry>;
}

export interface HardwareInfo {
  ram_gb: number;
  gpu_detected: boolean;
  gpu_names: string[];
  apple_silicon: string | null;
  available_providers: string[];
  recommended_tier: ModelTier;
}

export interface HardwareResponse {
  success: boolean;
  data: HardwareInfo;
}

export interface ModelDownloadProgressDownloadingMessage {
  status: 'downloading';
  model_key: string;
  model_index: number;
  total_models: number;
  percent: number;
  downloaded: number;
  total: number;
}

export interface ModelDownloadProgressCompleteMessage {
  status: 'complete';
  model_key?: string;
}

export interface ModelDownloadProgressErrorMessage {
  status: 'error';
  message?: string;
}

export type ModelDownloadProgressMessage =
  | ModelDownloadProgressDownloadingMessage
  | ModelDownloadProgressCompleteMessage
  | ModelDownloadProgressErrorMessage;

export const MODEL_TIER_LABELS: Record<ModelTier, string> = {
  nano: 'Nano (~20 MB)',
  small: 'Small (~72 MB)',
  medium: 'Medium (~154 MB)',
};

export const MODEL_TIER_DESCRIPTIONS: Record<ModelTier, string> = {
  nano: 'Fastest, lightest recommended for low RAM devices',
  small: 'Balanced accuracy and speed for most systems',
  medium: 'Best accuracy recommended for modern hardware',
};

export const SEMANTIC_BUNDLE_KEYS = [
  'siglip2_base_vision',
  'siglip2_base_text',
  'siglip2_base_tokenizer',
] as const;

export const SEMANTIC_BUNDLE_TITLE = 'Semantic Search';
export const SEMANTIC_BUNDLE_LABEL = 'Semantic Search (~1.5 GB)';
export const SEMANTIC_BUNDLE_DESCRIPTION =
  'Search photos by describing them in your own words. Downloads three model files; runs fully on-device.';

export const getModelTierLabel = (tier: ModelTier) => MODEL_TIER_LABELS[tier];

export const getModelTierDescription = (tier: ModelTier) =>
  MODEL_TIER_DESCRIPTIONS[tier];

export const isModelTier = (value: string): value is ModelTier =>
  (MODEL_TIERS as readonly string[]).includes(value);

export const normalizeModelTier = (
  value: string,
  fallback: ModelTier = 'small',
): ModelTier => (isModelTier(value) ? value : fallback);

export const getInstalledModelTiers = (
  models: Record<string, ModelEntry>,
): ModelTier[] => {
  return MODEL_TIERS.filter((tier) => {
    const objectModel = Object.values(models).find(
      (model) =>
        model.feature === 'object_detection' &&
        model.tier === tier &&
        model.installed,
    );
    const faceModel = Object.values(models).find(
      (model) =>
        model.feature === 'face_detection' &&
        model.tier === tier &&
        model.installed,
    );

    return Boolean(objectModel && faceModel);
  });
};

export const isSemanticSearchAvailable = (
  models: Record<string, ModelEntry>,
): boolean => {
  const semanticTextModels = Object.values(models).filter(
    (model) => model.feature === 'semantic_text',
  );
  if (semanticTextModels.length === 0) return false;
  return semanticTextModels.every((model) => model.installed === true);
};
