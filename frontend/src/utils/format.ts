/**
 * Utility formatting functions for currencies, percentages, and metrics.
 * Adheres to None != 0 data integrity policy.
 * Supports Trillions (T), Billions (B), Millions (M), Thousands (K) and multi-currency formatting.
 */

export function formatCurrency(
  val: number | string | null | undefined,
  currency: string = "USD"
): string {
  if (val == null || val === "" || isNaN(Number(val))) {
    return "N/A";
  }

  const num = Number(val);
  const cur = (currency || "USD").toUpperCase();

  let symbol = "$";
  if (cur === "EUR") symbol = "€";
  else if (cur === "GBP") symbol = "£";
  else if (cur === "INR") symbol = "₹";
  else if (cur === "JPY") symbol = "¥";
  else if (cur === "IDR") symbol = "IDR ";
  else if (cur === "USD") symbol = "$";
  else symbol = `${cur} `;

  return `${symbol}${num.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

export function formatCompactCurrency(
  val: number | string | null | undefined,
  currency: string = "USD",
  decimals: number = 1
): string {
  if (val == null || val === "" || isNaN(Number(val))) {
    return "N/A";
  }

  const num = Number(val);
  const cur = (currency || "USD").toUpperCase();

  let symbol = "$";
  if (cur === "EUR") symbol = "€";
  else if (cur === "GBP") symbol = "£";
  else if (cur === "INR") symbol = "₹";
  else if (cur === "JPY") symbol = "¥";
  else if (cur === "IDR") symbol = "IDR ";
  else if (cur === "USD") symbol = "$";
  else symbol = `${cur} `;

  const absNum = Math.abs(num);

  if (absNum >= 1_000_000_000_000) {
    return `${symbol}${(num / 1_000_000_000_000).toFixed(decimals)}T`;
  }
  if (absNum >= 1_000_000_000) {
    return `${symbol}${(num / 1_000_000_000).toFixed(decimals)}B`;
  }
  if (absNum >= 1_000_000) {
    return `${symbol}${(num / 1_000_000).toFixed(decimals)}M`;
  }
  if (absNum >= 1_000) {
    return `${symbol}${(num / 1_000).toFixed(decimals)}K`;
  }

  return `${symbol}${num.toLocaleString()}`;
}

export function formatPercent(
  val: number | string | null | undefined,
  decimals: number = 2
): string {
  if (val == null || val === "" || isNaN(Number(val))) {
    return "N/A";
  }
  const num = Number(val);
  return `${(num * 100).toFixed(decimals)}%`;
}
