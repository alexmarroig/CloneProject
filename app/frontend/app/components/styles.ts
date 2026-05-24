import type { CSSProperties } from "react";

export const panel: CSSProperties = {
  background: "var(--panel)",
  border: "1px solid var(--line)",
  borderRadius: 20,
  padding: 20,
  boxShadow: "0 18px 45px rgba(29, 27, 24, 0.08)",
};

export const inputStyle: CSSProperties = { width: "100%", padding: 10 };
export const primary: CSSProperties = {
  border: 0,
  borderRadius: 999,
  padding: "10px 16px",
  background: "var(--accent)",
  color: "white",
  cursor: "pointer",
};
export const ghost: CSSProperties = {
  border: "1px solid var(--line)",
  borderRadius: 999,
  padding: "8px 12px",
  background: "transparent",
  cursor: "pointer",
};
