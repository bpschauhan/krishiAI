import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@krishiai/shared-utils";

const buttonVariants = cva(
  "inline-flex h-10 items-center justify-center whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80"
      }
    },
    defaultVariants: {
      variant: "default"
    }
  }
);

interface ButtonProps
  extends VariantProps<typeof buttonVariants> {
  children?: any;
  className?: string;
  disabled?: boolean;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
}

function Button({
  children,
  className,
  disabled,
  onClick,
  type = "button",
  variant
}: ButtonProps) {
  const resolvedClassName = cn(buttonVariants({ variant, className }));

  return (
    <button className={resolvedClassName} disabled={disabled} onClick={onClick} type={type}>
      {children}
    </button>
  );
}

export { Button, buttonVariants };
export type { ButtonProps };
