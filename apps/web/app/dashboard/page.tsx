import { Card } from "@krishiai/ui";

type FarmerDashboard = {
  id: number;
  full_name: string;
  district: {
    id: number;
    name: string;
    state: string;
  };
  farm_count: number;
  plot_count: number;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const mockDashboard: FarmerDashboard = {
  id: 1,
  full_name: "Ramesh Kumar",
  district: {
    id: 1,
    name: "Lucknow",
    state: "Uttar Pradesh"
  },
  farm_count: 1,
  plot_count: 1
};

async function getDashboardData(): Promise<FarmerDashboard> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/farmers/1`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return mockDashboard;
    }
    return (await response.json()) as FarmerDashboard;
  } catch {
    return mockDashboard;
  }
}

export default async function DashboardPage() {
  const dashboard = await getDashboardData();

  return (
    <main className="min-h-screen bg-background px-5 py-8">
      <section className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Phase 1 Dashboard</p>
          <h1 className="text-3xl font-semibold text-foreground">Farmer overview</h1>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <DashboardMetric label="Farmer Name" value={dashboard.full_name} />
          <DashboardMetric label="District" value={dashboard.district.name} />
          <DashboardMetric label="Farm Count" value={dashboard.farm_count.toString()} />
          <DashboardMetric label="Plot Count" value={dashboard.plot_count.toString()} />
        </div>
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
