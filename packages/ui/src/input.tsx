import { cn } from "@krishiai/shared-utils";

interface InputProps {
  className?: string;
  name?: string;
  placeholder?: string;
  required?: boolean;
  type?: string;
  value?: string;
  onChange?: (event: any) => void;
}

function Input({
  className,
  name,
  onChange,
  placeholder,
  required,
  type = "text",
  value
}: InputProps) {
  return (
    <input
      className={cn(
        "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      name={name}
      onChange={onChange}
      placeholder={placeholder}
      required={required}
      type={type}
      value={value}
    />
  );
}

export { Input };
export type { InputProps };
