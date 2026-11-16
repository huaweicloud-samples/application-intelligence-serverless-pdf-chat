/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_ENDPOINT: string;
  readonly VITE_APIG_APP_CODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
