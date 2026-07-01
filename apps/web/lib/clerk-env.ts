const requiredClerkEnv = [
  "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY",
  "CLERK_SECRET_KEY",
  "NEXT_PUBLIC_CLERK_SIGN_IN_URL",
  "NEXT_PUBLIC_CLERK_SIGN_UP_URL"
] as const;

export function assertClerkEnv() {
  const missing = requiredClerkEnv.filter((key) => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(
      `Missing Clerk environment variables: ${missing.join(", ")}. ` +
        "Set them in apps/web/.env.local before starting the web app."
    );
  }
}
