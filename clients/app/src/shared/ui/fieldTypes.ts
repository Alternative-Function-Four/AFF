export interface FieldOption<T extends string> {
  label: string;
  value: T;
  description?: string;
}

export interface EntityOption {
  id: string;
  label: string;
  description?: string;
}
