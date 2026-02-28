export function dedupeIds(ids: string[]): string[] {
  return Array.from(new Set(ids));
}

export function toggleSelection(current: string[], id: string): string[] {
  if (current.includes(id)) {
    return current.filter((value) => value !== id);
  }
  return [...current, id];
}

export function setAllSelections(availableIds: string[], shouldSelectAll: boolean): string[] {
  if (!shouldSelectAll) {
    return [];
  }
  return dedupeIds(availableIds);
}
