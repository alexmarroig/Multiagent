export function formatDistanceToNow(date: Date | string | number) {
  const value = new Date(date);
  return Number.isNaN(value.getTime()) ? '' : value.toISOString();
}
