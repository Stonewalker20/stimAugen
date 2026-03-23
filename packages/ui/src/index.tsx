import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

export function Card({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={`ui-card ${className ?? ""}`.trim()}>{children}</section>;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  busy = false,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
  busy?: boolean;
}) {
  return (
    <button
      {...props}
      className={`ui-button ui-button-${variant} ${size === "sm" ? "ui-button-sm" : ""} ${props.className ?? ""}`.trim()}
      disabled={busy || props.disabled}
    >
      {busy ? "Working…" : children}
    </button>
  );
}

export function SectionTitle({
  title,
  subtitle,
  compact = false,
}: {
  title: string;
  subtitle?: string;
  compact?: boolean;
}) {
  return (
    <div className={`ui-section-title ${compact ? "ui-compact" : ""}`.trim()}>
      {compact ? <h3>{title}</h3> : <h2>{title}</h2>}
      {subtitle ? <p>{subtitle}</p> : null}
    </div>
  );
}

export function Field({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <label className="ui-field">
      <span className="ui-field-label">{label}</span>
      {description ? <p className="ui-field-description">{description}</p> : null}
      {children}
    </label>
  );
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`ui-input ${props.className ?? ""}`.trim()} />;
}

export function TextArea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`ui-textarea ${props.className ?? ""}`.trim()} />;
}

export function Slider({
  value,
  onChange,
  ...props
}: Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "value" | "onChange"> & {
  value: number;
  onChange(value: number): void;
}) {
  return (
    <input
      {...props}
      className={`ui-range ${props.className ?? ""}`.trim()}
      type="range"
      value={value}
      onChange={(event) => onChange(Number(event.target.value))}
    />
  );
}

export function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange(next: boolean): void;
}) {
  return (
    <button
      type="button"
      className={`ui-toggle ${checked ? "is-active" : ""}`.trim()}
      onClick={() => onChange(!checked)}
      aria-pressed={checked}
    >
      <span className="ui-toggle-handle" />
    </button>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "success" | "warning" | "danger" | "neutral";
}) {
  return <span className={`ui-badge ui-badge-${tone}`}>{children}</span>;
}

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="ui-progress-track" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
      <div className="ui-progress-value" style={{ width: `${value}%` }} />
    </div>
  );
}

export function Spinner() {
  return <div className="ui-spinner" aria-label="Loading" />;
}
