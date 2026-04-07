import "dotenv/config";
import express from "express";
import { toNodeHandler } from "better-auth/node";
import { auth } from "./auth.js";

const internalSecret = process.env.AUTH_INTERNAL_SECRET ?? "";
const port = Number(process.env.PORT ?? "3001");

function toWebHeaders(headers: express.Request["headers"]) {
  const normalized = new Headers();

  Object.entries(headers).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((entry) => normalized.append(key, entry));
      return;
    }

    if (typeof value === "string") {
      normalized.set(key, value);
    }
  });

  return normalized;
}

const app = express();

app.get("/internal/session", async (request, response) => {
  if (internalSecret && request.header("x-internal-auth-secret") !== internalSecret) {
    response.status(403).json({ detail: "Forbidden" });
    return;
  }

  const session = await auth.api.getSession({
    headers: toWebHeaders(request.headers),
  });

  if (!session) {
    response.status(401).json({ detail: "Authentication required" });
    return;
  }

  response.setHeader("Cache-Control", "no-store");
  response.json(session);
});

app.all("/api/auth", toNodeHandler(auth));
app.all("/api/auth/{*authPath}", toNodeHandler(auth));

app.listen(port, () => {
  // Keep startup logs compact but explicit for local debugging.
  console.log(`Auth service listening on port ${port}`);
});
