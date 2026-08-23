export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
export function requiresApproval(level: RiskLevel) { return level !== "LOW" }
