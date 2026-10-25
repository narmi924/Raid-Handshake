export interface Config {
  twitch_client_id: string;
  transcription_model: string;
  summary_model: string;
  commands: string;
  rule: string;
  template: string;
  language: string;
  preapproved_enabled: boolean;
  audio_device_id: string;
  chatters_poll_seconds: number;
  transcript_window_seconds: number;
}
export interface MetricSample {
  minute: number;
  scheduled_at: number;
  observed_at: number | null;
  population: number | null;
  connected: number | null;
  spoken: number | null;
  follows: number | null;
  error: string | null;
  chat_complete: boolean;
  cohort_complete: boolean;
}
export interface Raid {
  id: string;
  started_at: number;
  received_at: number;
  source_id: string;
  source_login: string;
  source_name: string;
  viewers: number;
  baseline_at: number | null;
  population: number | null;
  cohort_complete: boolean;
  cohort_finalized: boolean;
  overlap: boolean;
  draft_id: string | null;
  guest: {
    name: string;
    login: string;
    title: string;
    category: string;
    image: string;
    clips: { id: string; title: string; url: string; created_at: string }[];
    error: string | null;
  };
  learning: {
    status: string;
    messages: number;
    authors?: number;
    note?: string;
    emotes?: { id: string; name: string; count: number; users: number }[];
    tokens?: { text: string; count: number; users: number }[];
  };
  samples: MetricSample[];
}
export interface Draft {
  id: string;
  raid_id: string;
  text: string;
  text_hash: string;
  created_at: number;
  status: string;
  previewed_at: number | null;
  message_id: string | null;
  error: string | null;
  sent_at: number | null;
  automatic: boolean;
}
export interface State {
  now: number;
  config: Config;
  template_hash: string;
  user: {
    id: string;
    login: string;
    display_name: string;
    profile_image_url: string;
  } | null;
  device_login: {
    user_code: string;
    verification_uri: string;
    expires_at: number;
    status: string;
  } | null;
  login_error: string | null;
  health: {
    eventsub: string;
    eventsub_error: string | null;
    chatters: string;
    chatters_error: string | null;
    baseline_at: number | null;
    chatters_count: number | null;
    openai_configured: boolean;
    credential_storage: string;
    global_hotkey: boolean;
    hotkey_error: string | null;
  };
  audio: {
    active: boolean;
    level: number;
    error: string | null;
    last_chunk: number | null;
    queue: number;
  };
  summary: {
    activity: string;
    created_at: number;
    window_start: number;
    window_end: number;
    evidence: string[];
  } | null;
  summary_ready: boolean;
  summary_running: boolean;
  summary_error: string | null;
  transcript: { at: number; text: string }[];
  raids: Raid[];
  drafts: Draft[];
  activity: { at: number; kind: string; message: string }[];
}
export interface OverlayState {
  now: number;
  raids: Raid[];
  channel: string | null;
  landing: string | null;
  eventsub: string;
}
