// Application configuration.
//
// Authentication is provided by APIG App authentication. The front end only needs:
//   - the API base URL (APIG stage URL)
//   - an optional AppCode header (X-Apig-AppCode) when APIG uses simple App
//     authentication
//   - a per-browser user id, stored in localStorage, used to scope documents
//
// All values are injected at build time via Vite environment variables
// (see .env.example).

const API_ENDPOINT: string = import.meta.env.VITE_API_ENDPOINT || "";

const APIG_APP_CODE: string = import.meta.env.VITE_APIG_APP_CODE || "";

const USER_ID_KEY = "docchat_user_id";

function getUserId(): string {
  let id = localStorage.getItem(USER_ID_KEY);
  if (!id) {
    id =
      (typeof crypto !== "undefined" && crypto.randomUUID && crypto.randomUUID()) ||
      Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem(USER_ID_KEY, id);
  }
  return id;
}

export { API_ENDPOINT, APIG_APP_CODE, getUserId };
