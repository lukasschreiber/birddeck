// Hide line-break hyphens before lowercase letters in webapp labels.
export const displayName = (name: string): string =>
  name.replace(/-(?=\p{Ll})/gu, "");
