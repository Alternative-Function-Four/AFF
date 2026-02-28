const DATETIME_OPTIONS: Intl.DateTimeFormatOptions = {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Asia/Singapore"
};

const CURRENCY_OPTIONS: Intl.NumberFormatOptions = {
  style: "currency",
  currency: "SGD",
  maximumFractionDigits: 0
};

const DISTANCE_OPTIONS: Intl.NumberFormatOptions = {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1
};

export function formatDateTimeSg(value: string): string {
  return new Intl.DateTimeFormat("en-SG", DATETIME_OPTIONS).format(new Date(value));
}

export function formatSgd(min?: number | null, max?: number | null): string {
  if (min == null && max == null) {
    return "Price unavailable";
  }
  const formatter = new Intl.NumberFormat("en-SG", CURRENCY_OPTIONS);
  if (min != null && max != null) {
    return `${formatter.format(min)} - ${formatter.format(max)}`;
  }
  if (min != null) {
    return `From ${formatter.format(min)}`;
  }
  return `Up to ${formatter.format(max as number)}`;
}

export function formatDistanceKm(value: number): string {
  const formatted = new Intl.NumberFormat("en-SG", DISTANCE_OPTIONS).format(value);
  return `${formatted} km`;
}
