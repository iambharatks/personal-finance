// Indian numbering throughout: ₹1,23,456 and ₹1.2L / ₹1.2Cr.
const rupees = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});
const rupeesAndPaise = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const compact = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  notation: "compact",
  maximumFractionDigits: 1,
});

export const inr = (value: number) => rupees.format(value);
export const inrExact = (value: number) => rupeesAndPaise.format(value);
export const inrCompact = (value: number) => compact.format(value);

export const percent = (ratio: number | null | undefined, digits = 1) =>
  ratio == null ? "–" : `${(ratio * 100).toFixed(digits)}%`;

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2025-04" -> "Apr 25" */
export const monthLabel = (month: string) =>
  `${MONTHS[Number(month.slice(5, 7)) - 1]} ${month.slice(2, 4)}`;

/** "2025-04-03" -> "3 Apr" */
export const shortDayLabel = (day: string) =>
  `${Number(day.slice(8, 10))} ${MONTHS[Number(day.slice(5, 7)) - 1]}`;

/** "2025-04-03" -> "3 Apr 2025" (no Date object, so no timezone surprises) */
export const dayLabel = (day: string) =>
  `${Number(day.slice(8, 10))} ${MONTHS[Number(day.slice(5, 7)) - 1]} ${day.slice(0, 4)}`;
