import { Button, Card } from "@krishiai/ui";
import Link from "next/link";

export default function UnauthorizedPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-5 py-10">
      <Card className="w-full max-w-md p-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Access denied</p>
            <h1 className="text-2xl font-semibold text-foreground">Unauthorized</h1>
            <p className="text-sm leading-6 text-muted-foreground">
              Your account does not have permission to open this area.
            </p>
          </div>
          <Button>
            <Link href="/dashboard">Back to dashboard</Link>
          </Button>
        </div>
      </Card>
    </main>
  );
}
