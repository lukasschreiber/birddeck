import {
  Autocomplete,
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { TreeViewExpandIcon } from "@mui/x-tree-view/icons";
import type { Entry, EntryType } from "../types";
import type { Editor } from "../hooks/useProfileEditor";
import { KeyPreview } from "./KeyPreview";
import { ImageThumbnail } from "./ImageThumbnail";
import { BackgroundSelector } from "./BackgroundSelector";
import { displayName } from "../displayName";
import { sortEntries } from "../sortEntries";
import { CountrySelector } from "./CountrySelector";

export function EntryForm({ editor: e }: { editor: Editor }) {
  const icon = e.form.icon.trim();
  const validIcon =
    e.form.type === "uncertain" || !icon || Object.hasOwn(e.icons, icon);
  const parent = e.destination ?? (e.selected.slice(0, -1).join(".") || "root");
  const destinations = [
    {
      id: "root",
      label: "Profile root",
      title: e.state?.config.profile.name || "Vogel",
    },
  ];
  function collectGroups(
    items: Entry[],
    path: number[] = [],
    labels: string[] = [],
  ) {
    for (const { entry, index } of sortEntries(items)) {
      const childPath = [...path, index];
      if (
        entry.type !== "group" ||
        e.selected.every((value, i) => childPath[i] === value)
      )
        continue;
      const childLabels = [...labels, displayName(entry.title || "Uncertain")];
      destinations.push({
        id: childPath.join("."),
        label: childLabels.join(" / "),
        title: entry.title || "Vogel",
      });
      collectGroups(entry.items || [], childPath, childLabels);
    }
  }
  if (e.state && !e.adding) collectGroups(e.state.config.profile.items);
  return (
    <Paper variant="outlined" sx={{ p: 2 }} component="form" onSubmit={e.save}>
      <Stack spacing={2}>
        <KeyPreview
          entry={e.form}
          parentTitle={
            (!e.adding &&
              destinations.find((group) => group.id === parent)?.title) ||
            e.breadcrumbs[
              e.adding ? e.breadcrumbs.length - 1 : e.breadcrumbs.length - 2
            ] ||
            "Vogel"
          }
        />
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          Entry details
        </Typography>
        {!e.adding && (
          <TextField
            size="small"
            select
            label="Parent group"
            value={parent}
            onChange={(event) => e.regroup(event.target.value)}
            disabled={e.saving}
            helperText="Choose a group, then save to move this entry."
          >
            {destinations.map((group) => (
              <MenuItem key={group.id} value={group.id}>
                {group.label}
              </MenuItem>
            ))}
          </TextField>
        )}
        <TextField
          size="small"
          select
          label="Entry type"
          value={e.form.type}
          disabled={!e.adding || e.saving}
          onChange={(event) =>
            e.update("type", event.target.value as EntryType)
          }
        >
          {(["bird", "group", "uncertain"] as const).map((type) => (
            <MenuItem key={type} value={type}>
              {type[0].toUpperCase() + type.slice(1)}
            </MenuItem>
          ))}
        </TextField>
        {e.form.type !== "uncertain" && (
          <>
            <TextField
              size="small"
              label="Display name"
              value={e.form.title}
              onChange={(event) => e.update("title", event.target.value)}
              required
              disabled={e.saving}
            />
            <Autocomplete
              size="small"
              freeSolo
              options={Object.keys(e.icons)}
              inputValue={e.form.icon}
              onInputChange={(_, value) => e.update("icon", value)}
              disabled={e.saving}
              renderOption={(props, option) => {
                const { key, ...optionProps } = props;
                return (
                  <Box component="li" key={key} {...optionProps}>
                    <Stack
                      direction="row"
                      spacing={1.5}
                      sx={{ alignItems: "center" }}
                    >
                      <ImageThumbnail kind="icon" value={option} />
                      <Typography variant="body2">{option}</Typography>
                    </Stack>
                  </Box>
                );
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  slotProps={{
                    ...params.slotProps,
                    input: {
                      ...params.slotProps.input,
                      startAdornment: (
                        <>
                          {validIcon && icon && (
                            <ImageThumbnail
                              kind="icon"
                              value={icon}
                              size={24}
                            />
                          )}
                          {params.slotProps.input.startAdornment}
                        </>
                      ),
                    },
                  }}
                  label="Icon ID"

                  error={!validIcon}
                  helperText={
                    icon
                      ? validIcon
                        ? "Icon found"
                        : "Choose an ID from data/icons.json"
                      : e.form.type === "bird"
                        ? "Optional. Leave empty to omit the eBird action."
                        : "Optional for groups."
                  }
                />
              )}
            />
            {e.form.type === "group" && (
              <>
                <TextField
                  size="small"
                  label="Lightroom keyword (optional)"
                  value={e.form.tag}
                  onChange={(event) => e.update("tag", event.target.value)}
                  disabled={e.saving}
                />
                <BackgroundSelector
                  value={e.form.bg}
                  onChange={(value) => e.update("bg", value)}
                  disabled={e.saving}
                />
              </>
            )}
            {icon && (
              <Box
                component="details"
                sx={{
                  "&[open] .rotation-chevron": { transform: "rotate(90deg)" },
                }}
              >
                <Typography
                  component="summary"
                  variant="body2"
                  sx={{
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: 0.5,
                    minHeight: 30,
                    borderRadius: 1,
                    "&::-webkit-details-marker": { display: "none" },
                    "&:hover": { bgcolor: "action.hover" },
                  }}
                >
                  <TreeViewExpandIcon
                    className="rotation-chevron"
                    sx={{ fontSize: 20, flexShrink: 0 }}
                  />
                  Image rotation
                  {e.form.rotation ? ` (${e.form.rotation}°)` : ""}
                </Typography>
                <TextField
                  sx={{ mt: 1, width: 220 }}
                  size="small"
                  type="number"
                  label="Rotation (degrees)"
                  value={e.form.rotation}
                  onChange={(event) =>
                    e.update("rotation", Number(event.target.value))
                  }
                  slotProps={{ htmlInput: { min: -180, max: 180, step: 1 } }}
                  helperText="Positive rotates clockwise. 0 keeps the original."
                  disabled={e.saving}
                />
              </Box>
            )}
            <Stack direction="row">
              <FormControlLabel
                label="Favorite"
                control={
                  <Checkbox
                    size="small"
                    checked={e.form.favorite}
                    onChange={(event) =>
                      e.update("favorite", event.target.checked)
                    }
                    disabled={e.saving}
                  />
                }
              />
              <FormControlLabel
                label="Exotic"
                control={
                  <Checkbox
                    size="small"
                    checked={e.form.exotic}
                    onChange={(event) =>
                      e.update("exotic", event.target.checked)
                    }
                    disabled={e.saving}
                  />
                }
              />
            </Stack>
            {e.form.exotic && (
              <CountrySelector
                value={e.form.country}
                onChange={(code) => e.update("country", code)}
                disabled={e.saving}
              />
            )}
          </>
        )}
        <Stack direction="row" sx={{ justifyContent: "flex-end" }} spacing={1}>
          {!e.adding && (
            <Box sx={{ mr: "auto !important" }}>
              <Button
                size="small"
                color="error"
                onClick={e.deleteEntry}
                disabled={e.saving || !e.canDelete}
              >
                Delete entry
              </Button>
              {!e.canDelete && (
                <Typography
                  variant="caption"
                  sx={{ display: "block" }}
                  color="text.secondary"
                >
                  Delete all children first.
                </Typography>
              )}
            </Box>
          )}
          <Button size="small" onClick={e.reset} disabled={e.saving}>
            Reset
          </Button>
          <Button
            size="small"
            type="submit"
            variant="contained"
            disabled={e.saving || !validIcon}
          >
            {e.saving ? "Saving..." : "Save entry"}
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
