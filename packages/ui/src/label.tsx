import { cn } from "@krishiai/shared-utils";

interface LabelProps {
  children?: any;
  className?: string;
  htmlFor?: string;
}

function Label({ children, className, htmlFor }: LabelProps) {
  return (
    <label className={cn("text-sm font-medium leading-none text-foreground", className)} htmlFor={htmlFor}>
      {children}
    </label>
  );
}

export { Label };
export type { LabelProps };
