import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import { Sidebar } from "./components/Sidebar";
import { EntryForm } from "./components/EntryForm";
import { useProfileEditor } from "./hooks/useProfileEditor";
import { displayName } from "./displayName";

export default function App() {
  const editor = useProfileEditor();
  const title = editor.adding
    ? "Add entry"
    : editor.root
      ? "Profile entries"
      : editor.entry?.title || "Uncertain";
  const canAdd =
    !!editor.state &&
    !editor.adding &&
    (editor.root || ("type" in editor.entry! && editor.entry.type === "group"));
  return (
    <Box sx={{ display: "flex", height: "100dvh", overflow: "hidden" }}>
      <Sidebar editor={editor} />
      <Box
        component="main"
        sx={{ flex: 1, minWidth: 0, overflowY: "auto", p: { xs: 2, md: 3 } }}
      >
        <Stack spacing={2} sx={{ maxWidth: 720, mx: "auto" }}>
          <Stack
            direction="row"
            spacing={2}
            sx={{ justifyContent: "space-between", alignItems: "center" }}
          >
            <Box>
              <Typography variant="h5">{displayName(title)}</Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 0.5 }}
              >
                {editor.breadcrumbs.map(displayName).join(" / ")}
              </Typography>
            </Box>
            <Button
              size="small"
              variant="outlined"
              onClick={editor.add}
              disabled={!canAdd}
              sx={{ flexShrink: 0 }}
            >
              Add child
            </Button>
          </Stack>
          <Alert severity={editor.notice.severity}>{editor.notice.text}</Alert>
          {!editor.root && <EntryForm editor={editor} />}
        </Stack>
      </Box>
    </Box>
  );
}
