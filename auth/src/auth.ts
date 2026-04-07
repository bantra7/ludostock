import "dotenv/config";
import { betterAuth } from "better-auth";

function requireEnv(name: string) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export const auth = betterAuth({
  baseURL: requireEnv("BETTER_AUTH_URL"),
  secret: requireEnv("BETTER_AUTH_SECRET"),
  socialProviders: {
    google: {
      clientId: requireEnv("GOOGLE_CLIENT_ID"),
      clientSecret: requireEnv("GOOGLE_CLIENT_SECRET"),
      prompt: "select_account",
    },
  },
  session: {
    cookieCache: {
      enabled: true,
      maxAge: 60 * 60 * 24 * 7,
      strategy: "compact",
      refreshCache: true,
    },
  },
  account: {
    storeStateStrategy: "cookie",
    storeAccountCookie: true,
  },
});
