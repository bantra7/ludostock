import { createAuthClient } from "better-auth/react";

const AUTH_BASE_URL = window.location.origin;

export const authClient = createAuthClient({
  baseURL: AUTH_BASE_URL,
  fetchOptions: {
    credentials: "include",
  },
  sessionOptions: {
    refetchOnWindowFocus: true,
  },
});
