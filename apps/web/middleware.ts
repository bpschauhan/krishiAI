import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { assertClerkEnv } from "./lib/clerk-env";

const isProtectedRoute = createRouteMatcher(["/dashboard(.*)", "/profile(.*)", "/onboarding(.*)"]);

export default clerkMiddleware(async (auth, request) => {
  assertClerkEnv();

  if (isProtectedRoute(request)) {
    await auth.protect({ unauthenticatedUrl: new URL("/login", request.url).toString() });
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)"
  ]
};
