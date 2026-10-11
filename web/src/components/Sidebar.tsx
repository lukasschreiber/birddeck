import { useState } from "react";
import {
  Box,
  Chip,
  Divider,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { TreeItem } from "@mui/x-tree-view/TreeItem";
import type { Entry } from "../types";
import type { Editor } from "../hooks/useProfileEditor";

const count = (items: Entry[]): number =>
  items.reduce((total, item) => total + 1 + count(item.items || []), 0);

export function Sidebar({ editor }: { editor: Editor }) {
  const [query, setQuery] = useState("");
  const search = query.trim().toLowerCase();

  const matches = (entry: Entry): boolean =>
    (entry.title || "Uncertain").toLowerCase().includes(search) ||
    (entry.icon || "").includes(search) ||
    (entry.items || []).some(matches);
  const searchExpanded: string[] = ["root"];

  function render(items: Entry[], parent: number[] = []): React.ReactNode {
    return items.map((entry, index) => {
      if (search && !matches(entry)) return null;
      const path = [...parent, index];
      const id = path.join(".");
      if (entry.type === "group") searchExpanded.push(id);
      return (
        <TreeItem key={id} itemId={id} label={entry.title || "Uncertain"}>
          {entry.type === "group" ? render(entry.items || [], path) : null}
        </TreeItem>
      );
    });
  }
  const children = editor.state
    ? render(editor.state.config.profile.items)
    : null;
  return (
    <Box
      component="aside"
      sx={{
        width: { xs: 230, md: 280 },
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        borderRight: 1,
        borderColor: "divider",
      }}
    >
      <Stack spacing={1.5} sx={{ p: 2 }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {editor.state?.config.profile.name || "BirdDeck"}
          </Typography>
          {editor.state && (
            <Chip
              size="small"
              label={count(editor.state.config.profile.items)}
            />
          )}
        </Stack>
        <TextField
          size="small"
          label="Search entries or icons"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </Stack>
      <Divider />
      <Box
        component="nav"
        aria-label="Entry hierarchy"
        sx={{ flex: 1, minHeight: 0, overflowY: "auto", p: 1 }}
      >
        <SimpleTreeView
          expansionTrigger="iconContainer"
          selectedItems={
            editor.adding
              ? null
              : editor.selected.length
                ? editor.selected.join(".")
                : "root"
          }
          expandedItems={search ? searchExpanded : editor.expanded}
          onExpandedItemsChange={(_, ids) => editor.setExpanded(ids)}
          onSelectedItemsChange={(_, id) => {
            if (id)
              editor.choose(id === "root" ? [] : id.split(".").map(Number));
          }}
          sx={{
            "& .MuiTreeItem-content": { py: 0.25, minHeight: 30 },
            "& .MuiTreeItem-label": { fontSize: "0.875rem" },
          }}
        >
          <TreeItem itemId="root" label="Profile root">
            {children}
          </TreeItem>
        </SimpleTreeView>
      </Box>
    </Box>
  );
}
