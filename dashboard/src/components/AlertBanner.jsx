const TYPE_STYLES = {
  error: { bg: "#3a1f1f", border: "#e53935" },
  warning: { bg: "#3a2f1f", border: "#fb8c00" },
  success: { bg: "#1f3a24", border: "#43a047" },
};

export default function AlertBanner({ type = "warning", message, onDismiss }) {
  const style = TYPE_STYLES[type] || TYPE_STYLES.warning;
  return (
    <div className="alert-banner" style={{ background: style.bg, borderColor: style.border }}>
      <span>{message}</span>
      <button className="icon-btn" onClick={onDismiss}>✕</button>
    </div>
  );
}
