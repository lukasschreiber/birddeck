import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { displayName } from "../displayName";
import type {
  Entry,
  EntryForm,
  IconMap,
  Notice,
  Profile,
  Snapshot,
} from "../types";

const blank = (): EntryForm => ({
  type: "bird",
  title: "",
  icon: "",
  rotation: 0,
  tag: "",
  bg: "",
  favorite: false,
  exotic: false,
  country: "",
  nabu: "",
});

const toForm = (entry: Entry | Profile): EntryForm =>
  ({ ...blank(), ...entry }) as EntryForm;

const entryAt = (snapshot: Snapshot, path: number[]): Entry | Profile =>
  path.reduce<Entry | Profile>(
    (entry, index) => entry.items![index],
    snapshot.config.profile,
  );

export function useProfileEditor() {
  const [state, setState] = useState<Snapshot | null>(null);
  const [icons, setIcons] = useState<IconMap>({});
  const [selected, setSelected] = useState<number[]>([]);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState<EntryForm>(blank);
  const [dirty, setDirty] = useState(false);
  const [destination, setDestination] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string[]>(["root"]);
  const [notice, setNotice] = useState<Notice>({
    severity: "info",
    text: "Select an entry or add a child to a group.",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([api<Snapshot>("/api/config"), api<IconMap>("/api/icons")])
      .then(([snapshot, mapping]) => {
        setState(snapshot);
        setIcons(mapping);
      })
      .catch((error: Error) =>
        setNotice({ severity: "error", text: error.message }),
      );
  }, []);

  useEffect(() => {
    const handler = (event: BeforeUnloadEvent) => {
      if (dirty) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  const discard = () =>
    !dirty || window.confirm("Discard unsaved form changes?");

  const choose = (path: number[]) => {
    if (!state || !discard()) return;
    setSelected(path);
    setDestination(null);
    setAdding(false);
    setForm(toForm(entryAt(state, path)));
    setDirty(false);
  };

  const add = () => {
    if (discard()) {
      setAdding(true);
      setDestination(null);
      setForm(blank());
      setDirty(false);
    }
  };

  const reset = () => {
    if (state && discard()) {
      setForm(adding ? blank() : toForm(entryAt(state, selected)));
      setDestination(null);
      setDirty(false);
    }
  };

  const update = <K extends keyof EntryForm>(key: K, value: EntryForm[K]) => {
    setForm((previous) => ({ ...previous, [key]: value }));
    setDirty(true);
  };

  const regroup = (value: string) => {
    setDestination(value);
    setDirty(true);
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!state) return;
    setSaving(true);
    try {
      const result = await api<Snapshot>("/api/entry", {
        revision: state.revision,
        action: adding ? "add" : "update",
        path: selected,
        entry: form,
        ...(!adding && destination !== null
          ? {
              destination:
                destination === "root"
                  ? []
                  : destination.split(".").map(Number),
            }
          : {}),
      });
      const path = result.selected!;
      setState(result);
      setSelected(path);
      setDestination(null);
      setAdding(false);
      setForm(toForm(entryAt(result, path)));
      setDirty(false);
      setExpanded((previous) =>
        Array.from(
          new Set([
            "root",
            ...(destination === null ? previous : []),
            ...path.map((_, index) => path.slice(0, index + 1).join(".")),
          ]),
        ),
      );
      setNotice({
        severity: "success",
        text: "Entry saved to your YAML configuration.",
      });
    } catch (error) {
      setNotice({
        severity: "error",
        text: error instanceof Error ? error.message : "Save failed",
      });
    } finally {
      setSaving(false);
    }
  };

  const root = !selected.length && !adding;
  const entry = state ? entryAt(state, selected) : null;
  const canDelete =
    !!entry && !adding && !!selected.length && !entry.items?.length;
  const deleteEntry = async () => {
    if (!state || !canDelete || saving) return;
    const name = displayName(entry?.title || "Uncertain");
    if (
      !window.confirm(
        `Delete "${name}"?${dirty ? " Unsaved changes will be discarded." : ""}`,
      )
    )
      return;
    setSaving(true);
    try {
      const result = await api<Snapshot>("/api/entry", {
        revision: state.revision,
        action: "delete",
        path: selected,
      });
      const path = result.selected!;
      setState(result);
      setSelected(path);
      setDestination(null);
      setForm(toForm(entryAt(result, path)));
      setDirty(false);
      setExpanded([
        "root",
        ...path.map((_, index) => path.slice(0, index + 1).join(".")),
      ]);
      setNotice({
        severity: "success",
        text: `Deleted "${name}" from your YAML configuration.`,
      });
    } catch (error) {
      setNotice({
        severity: "error",
        text: error instanceof Error ? error.message : "Delete failed",
      });
    } finally {
      setSaving(false);
    }
  };
  const breadcrumbs = state
    ? [
        state.config.profile.name,
        ...selected.map(
          (_, index) =>
            entryAt(state, selected.slice(0, index + 1)).title || "Uncertain",
        ),
      ]
    : [];

  return {
    state,
    destination,
    regroup,
    icons,
    selected,
    adding,
    form,
    expanded,
    setExpanded,
    notice,
    saving,
    root,
    canDelete,
    deleteEntry,
    entry,
    breadcrumbs,
    choose,
    add,
    reset,
    update,
    save,
  };
}

export type Editor = ReturnType<typeof useProfileEditor>;
