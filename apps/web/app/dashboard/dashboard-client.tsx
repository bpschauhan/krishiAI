"use client";

import { SignOutButton, UserButton, useAuth } from "@clerk/nextjs";
import { getDisplayName } from "@krishiai/auth";
import { Button, Card } from "@krishiai/ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { getMe } from "../../lib/auth-api";

export function DashboardClient() {
  const { getToken, isLoaded } = useAuth();
  const query = useQuery({
    queryKey: ["me"],
    enabled: isLoaded,
    queryFn: async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Missing Clerk session token");
      }
      return getMe(token);
    }
  });

  const user = query.data;

  return (
    <main className="min-h-screen bg-background px-5 py-8">
      <section className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Protected Dashboard</p>
            <h1 className="text-3xl font-semibold text-foreground">Farmer overview</h1>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="secondary">
              <Link href="/profile">Profile</Link>
            </Button>
            <SignOutButton>
              <Button variant="secondary">Logout</Button>
            </SignOutButton>
            <UserButton />
          </div>
        </header>

        {!isLoaded || query.isLoading ? (
          <Card className="p-5">
            <p className="text-sm text-muted-foreground">Loading secure session...</p>
          </Card>
        ) : null}

        {query.isError ? (
          <Card className="p-5">
            <p className="text-sm text-red-600">{query.error.message}</p>
          </Card>
        ) : null}

        {user ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2">
              <DashboardMetric label="Farmer Name" value={getDisplayName(user)} />
              <DashboardMetric label="District" value={user.profile?.district ?? "Not set"} />
              <DashboardMetric label="Farm Count" value="0" />
              <DashboardMetric label="Plot Count" value="0" />
            </div>
            <Card className="p-5">
              <p className="text-sm font-medium text-muted-foreground">Roles</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {user.roles.map((role) => (
                  <span className="rounded-md bg-secondary px-3 py-1 text-sm text-secondary-foreground" key={role.slug}>
                    {role.name}
                  </span>
                ))}
              </div>
            </Card>
          </>
        ) : null}
      </section>
    </main>
  );
}

function DashboardMetric({ label, value }: { label: string; value: string }) {
  return (
    <Card className="p-5">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-foreground">{value}</p>
    </Card>
  );
}
