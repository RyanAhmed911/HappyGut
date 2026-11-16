import * as Dialog from "@radix-ui/react-dialog";
import { cva, type VariantProps } from "class-variance-authority";
import { Minus, Plus, X } from "lucide-react";
import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/cn";
import { num } from "@/lib/format";

// ---------------------------------------------------------------- Button

const button = cva(
  "inline-flex items-center justify-center gap-2 rounded-2xl font-semibold transition active:scale-[0.98] disabled:pointer-events-none disabled:opacity-45 select-none",
  {
    variants: {
      variant: {
        primary: "bg-brand text-white shadow-float hover:bg-brand-deep",
        secondary: "bg-brand-soft text-brand-deep hover:bg-brand-soft/70",
        outline: "border border-line bg-card text-ink hover:bg-paper",
        ghost: "text-ink-soft hover:bg-paper-deep/70",
        danger: "bg-trigger text-white hover:bg-trigger/90",
      },
      size: { sm: "h-9 px-3.5 text-sm", md: "h-11 px-5 text-[15px]", lg: "h-14 px-6 text-base", icon: "h-10 w-10" },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export function Button({
  className,
  variant,
  size,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof button>) {
  return <button type="button" {...props} className={cn(button({ variant, size }), className)} />;
}

// ---------------------------------------------------------------- Card, Badge, titles

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-3xl border border-line/70 bg-card p-5 shadow-card", className)} {...props} />;
}

const badge = cva("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap", {
  variants: {
    tone: {
      neutral: "bg-paper-deep text-ink-soft",
      brand: "bg-brand-soft text-brand-deep",
      ok: "bg-ok-soft text-ok",
      caution: "bg-caution-soft text-caution",
      trigger: "bg-trigger-soft text-trigger",
      unsure: "bg-unsure-soft text-unsure",
      saffron: "bg-saffron-soft text-caution",
    },
  },
  defaultVariants: { tone: "neutral" },
});
export type Tone = NonNullable<VariantProps<typeof badge>["tone"]>;

export function Badge({ tone, className, ...props }: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badge>) {
  return <span className={cn(badge({ tone }), className)} {...props} />;
}

export function PageTitle({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <header className="mb-5 flex items-end justify-between gap-3">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight lg:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 text-[15px] text-ink-soft">{subtitle}</p>}
      </div>
      {action}
    </header>
  );
}

export function SectionTitle({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-2.5 mt-7 flex items-center justify-between gap-3">
      <h2 className="text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{children}</h2>
      {action}
    </div>
  );
}

// ---------------------------------------------------------------- Choice controls

export function Chip({
  selected,
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { selected?: boolean }) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      className={cn(
        "inline-flex min-h-10 items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-medium transition active:scale-[0.97]",
        selected ? "border-brand bg-brand text-white" : "border-line bg-card text-ink-soft hover:border-brand/40",
        className,
      )}
      {...props}
    />
  );
}

export function Segmented<T extends string | number>({
  value,
  options,
  onChange,
  className,
}: {
  value: T | null;
  options: { value: T; label: ReactNode; hint?: string }[];
  onChange: (v: T) => void;
  /** Grid column classes; by default all options sit in one row. */
  className?: string;
}) {
  return (
    <div role="radiogroup" className={cn("grid gap-2", className)} style={className ? undefined : { gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}>
      {options.map((o) => (
        <button
          key={String(o.value)}
          type="button"
          role="radio"
          aria-checked={value === o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            "flex min-h-12 flex-col items-center justify-center rounded-2xl border px-1.5 py-2 text-center text-[13px] font-semibold leading-tight transition active:scale-[0.97]",
            value === o.value ? "border-brand bg-brand text-white shadow-sm" : "border-line bg-card text-ink-soft hover:border-brand/40",
          )}
        >
          {o.label}
          {o.hint && <span className={cn("mt-0.5 text-[11px] font-normal", value === o.value ? "text-white/80" : "text-ink-faint")}>{o.hint}</span>}
        </button>
      ))}
    </div>
  );
}

export function Stepper({ value, min = 0, max = 30, onChange, label }: { value: number; min?: number; max?: number; onChange: (v: number) => void; label: string }) {
  const { i18n } = useTranslation();
  return (
    <div className="flex items-center gap-3" role="group" aria-label={label}>
      <Button variant="outline" size="icon" aria-label="−" disabled={value <= min} onClick={() => onChange(Math.max(min, value - 1))}>
        <Minus className="h-4 w-4" />
      </Button>
      <span className="tabular w-10 text-center text-2xl font-bold">{num(value, i18n.language)}</span>
      <Button variant="outline" size="icon" aria-label="+" disabled={value >= max} onClick={() => onChange(Math.min(max, value + 1))}>
        <Plus className="h-4 w-4" />
      </Button>
    </div>
  );
}

export function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="flex w-full items-center justify-between gap-4 rounded-2xl border border-line bg-card px-4 py-3 text-left text-[15px] font-medium"
    >
      <span>{label}</span>
      <span className={cn("relative h-6 w-11 shrink-0 rounded-full transition", checked ? "bg-brand" : "bg-paper-deep")}>
        <span className={cn("absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all", checked ? "left-[22px]" : "left-0.5")} />
      </span>
    </button>
  );
}

export function Tabs<T extends string>({ value, tabs, onChange }: { value: T; tabs: { value: T; label: ReactNode }[]; onChange: (v: T) => void }) {
  return (
    <div role="tablist" className="inline-flex w-full rounded-2xl bg-paper-deep p-1">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          role="tab"
          type="button"
          aria-selected={value === tab.value}
          onClick={() => onChange(tab.value)}
          className={cn(
            "flex-1 rounded-xl px-3 py-2 text-sm font-semibold transition",
            value === tab.value ? "bg-card text-ink shadow-sm" : "text-ink-faint hover:text-ink-soft",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- Sheet (bottom sheet on phones, dialog on desktop)

export function Sheet({
  open,
  onOpenChange,
  title,
  description,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-ink/40 backdrop-blur-[2px]" />
        <Dialog.Content
          aria-describedby={undefined}
          className="fixed inset-x-0 bottom-0 z-50 max-h-[90dvh] overflow-y-auto rounded-t-[28px] bg-card p-5 pb-8 shadow-2xl animate-rise sm:inset-auto sm:left-1/2 sm:top-1/2 sm:w-[min(92vw,460px)] sm:-translate-x-1/2 sm:-translate-y-1/2 sm:rounded-[28px]"
        >
          <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-line sm:hidden" />
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <Dialog.Title className="text-lg font-bold">{title}</Dialog.Title>
              {description && <p className="mt-0.5 text-sm text-ink-soft">{description}</p>}
            </div>
            <Dialog.Close className="rounded-full p-1.5 text-ink-faint hover:bg-paper-deep" aria-label="Close">
              <X className="h-5 w-5" />
            </Dialog.Close>
          </div>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ---------------------------------------------------------------- States

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton h-20", className)} aria-hidden />;
}

export function Empty({ icon, title, children }: { icon?: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center rounded-3xl border border-dashed border-line px-6 py-10 text-center">
      {icon && <div className="mb-3 text-ink-faint">{icon}</div>}
      <p className="font-semibold">{title}</p>
      {children && <div className="mt-1 text-sm text-ink-soft">{children}</div>}
    </div>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <div className="mb-5">
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <span className="text-[15px] font-semibold">{label}</span>
        {hint && <span className="text-xs text-ink-faint">{hint}</span>}
      </div>
      {children}
    </div>
  );
}

export const inputClass =
  "h-12 w-full rounded-2xl border border-line bg-card px-4 text-[15px] outline-none transition placeholder:text-ink-faint focus:border-brand focus:ring-4 focus:ring-brand/10";
