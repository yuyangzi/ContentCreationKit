// Type definitions for scenes.json consumed by Remotion components

export interface ColorTheme {
  primary: string;
  accent: string;
  text: string;
  background: string;
}

export interface Meta {
  article_title: string;
  article_source: string;
  output: string;
  aspect_ratio: string;
  width: number;
  height: number;
  fps: number;
  total_duration_frames: number;
  total_duration_seconds: number;
  total_duration_ms?: number;
  font_family: string;
  color_theme: ColorTheme;
}

export interface WordTimestamp {
  word: string;
  start_ms: number;
  end_ms: number;
}

export interface Narration {
  text: string;
  voice_file: string;
  // Backfilled by generate_audio.py; optional in agent-generated scenes.json
  voice_start_ms?: number;
  voice_end_ms?: number;
  timestamps?: WordTimestamp[];
}

export interface SearchKeywords {
  zh: string[];
  en: string[];
}

export interface AnimationConfig {
  type?: string;
  duration_frames?: number;
  direction?: string;
  stiffness?: number; damping?: number; mass?: number;
  scale_start?: number; scale_end?: number;
  pan_x?: number; pan_y?: number;
  stagger_delay_frames?: number;
  chars_per_frame?: number;
  from_scale?: number;
}

// Scene-specific data types
export interface TitleCardData { title: string; subtitle?: string; background?: string; }
export interface ChapterTitleData { chapter_number: number; title: string; subtitle?: string; }
export interface StockMediaItem { file: string; source: string; source_url?: string; type: "image" | "video"; width?: number; height?: number; relevance_score?: number; }
export interface TextOverlay { text: string; position?: string; font_size?: number; }
export interface StockFootageData { media?: StockMediaItem[]; text_overlays?: TextOverlay[]; }
export interface InfoCardColumn { title?: string; content: string; icon?: string; }
export interface InfoCardItem { text: string; highlight?: boolean; }
export interface InfoCardData { layout: string; columns?: InfoCardColumn[]; items?: InfoCardItem[]; quote?: string; quote_source?: string; }
export interface CodeBlockData { code: string; language: string; title?: string; }
export interface OutroData { cta_text: string; logo?: string; }

export interface Scene {
  id: string;
  type: string;
  duration_frames: number;
  search_keywords: SearchKeywords;
  data: Record<string, unknown>;
  animation?: AnimationConfig;
  narration: Narration;
}

export interface AudioConfig {
  voice_file: string;
  bgm_file: string | null;
  bgm_volume: number;
  voice_volume: number;
}

export interface CaptionConfig {
  enabled: boolean;
  style: string;
  font_size: number;
  position_y: number;
  active_color: string;
  inactive_color: string;
}

export interface ScenesJson {
  meta: Meta;
  scenes: Scene[];
  audio: AudioConfig;
  captions: CaptionConfig;
}