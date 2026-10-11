import type { Entry } from "./types";

// Match src/pagination.py while retaining YAML indices for selection and saves.
export function sortEntries(items: Entry[]) {
  return items
    .map((entry, index) => ({ entry, index }))
    .sort((a, b) => {
      const priority = (entry: Entry) => [
        Number(entry.type === "uncertain"),
        Number(!entry.favorite),
        Number(
          (entry.type === "bird" || entry.type === "group") && !!entry.exotic,
        ),
      ];
      const left = priority(a.entry);
      const right = priority(b.entry);
      for (let i = 0; i < left.length; i++) {
        if (left[i] !== right[i]) return left[i] - right[i];
      }
      const leftTitle = (a.entry.title || "").toLowerCase().replaceAll("-", "");
      const rightTitle = (b.entry.title || "")
        .toLowerCase()
        .replaceAll("-", "");
      return leftTitle < rightTitle ? -1 : leftTitle > rightTitle ? 1 : 0;
    });
}
