/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the API (empty => same-origin / dev proxy). */
  readonly VITE_API_BASE_URL?: string;
  /** Public base URL of the deployed site. */
  readonly VITE_PUBLIC_BASE_URL?: string;
  /** Web Health App URL. Empty => "Coming soon". */
  readonly VITE_HEALTH_APP_URL?: string;
  /** Apple App Store URL. Empty => "Coming soon". */
  readonly VITE_APP_STORE_URL?: string;
  /** Google Play URL. Empty => "Coming soon". */
  readonly VITE_PLAY_STORE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
