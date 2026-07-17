export function ProgressItem({ label, value, percent }: { label: string; value: string; percent: number }) {
  return (
    <div className="progress-item">
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <i
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <b style={{ width: `${percent}%` }} />
      </i>
    </div>
  );
}
