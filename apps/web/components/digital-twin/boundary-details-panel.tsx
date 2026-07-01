import type { BoundaryFeatureProperties } from "@krishiai/shared-types";
import { formatBoundaryArea, formatBoundaryHectares, formatBoundaryUpdatedAt } from "@krishiai/shared-utils";
import { Card } from "@krishiai/ui";

type BoundaryDetailsPanelProps = {
  selectedBoundary: BoundaryFeatureProperties | null;
};

export function BoundaryDetailsPanel({ selectedBoundary }: BoundaryDetailsPanelProps) {
  if (!selectedBoundary) {
    return (
      <Card className="p-5">
        <p className="text-sm font-medium text-muted-foreground">Boundary details</p>
        <p className="mt-3 text-sm text-muted-foreground">Select a visible farm or plot boundary to inspect it.</p>
      </Card>
    );
  }

  const title = selectedBoundary.boundaryKind === "farm" ? "Farm boundary" : "Plot boundary";

  return (
    <Card className="p-5">
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <div className="mt-4 grid gap-3 text-sm">
        <Detail label={selectedBoundary.boundaryKind === "farm" ? "Farm name" : "Plot name"} value={selectedBoundary.ownerName} />
        <Detail label="Area acres" value={formatBoundaryArea(selectedBoundary.areaAcres)} />
        <Detail label="Area hectares" value={formatBoundaryHectares(selectedBoundary.areaHectares)} />
        <Detail label="Last updated" value={formatBoundaryUpdatedAt(selectedBoundary.updatedAt)} />
      </div>
    </Card>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border pb-2 last:border-b-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium text-foreground">{value}</span>
    </div>
  );
}
