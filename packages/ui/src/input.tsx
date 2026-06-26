import { cn } from "@krishiai/shared-utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

function Input({
  className,
  type = "text",
  ...props
}: InputProps) {
  return (
    <input
      className={cn(
        "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      type={type}
      {...props}
    />
  );
}

export { Input };
export type { InputProps };
