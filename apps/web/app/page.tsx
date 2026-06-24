import type { HealthStatus } from "@krishiai/shared-types";
import { formatServiceStatus } from "@krishiai/shared-utils";
import { Button } from "@krishiai/ui";
import { Leaf } from "lucide-react";

const health: HealthStatus = {
  status: "ok",
  service: "krishiai-web"
};

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center gap-8 px-6 py-10">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Leaf className="size-5" aria-hidden="true" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">KrishiAI Platform</p>
        </div>
        <div className="max-w-3xl space-y-5">
          <h1 className="text-4xl font-semibold tracking-normal text-foreground sm:text-6xl">
            KrishiAI
          </h1>
          <p className="text-lg leading-8 text-muted-foreground">
            Agricultural operations foundation for farmers in Uttar Pradesh, India.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button>Open dashboard</Button>
          <p className="text-sm text-muted-foreground">{formatServiceStatus(health)}</p>
        </div>
      </section>
    </main>
  );
}
