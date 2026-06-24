import { cn } from "@krishiai/shared-utils";

interface CardProps {
  children?: any;
  className?: string;
}

function Card({ children, className }: CardProps) {
  return (
    <div className={cn("rounded-md border border-border bg-card text-card-foreground shadow-sm", className)}>
      {children}
    </div>
  );
}

export { Card };
export type { CardProps };
