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
import type { EntryType } from "../types";
import type { Editor } from "../hooks/useProfileEditor";
import { KeyPreview } from "./KeyPreview";
import { ImageThumbnail } from "./ImageThumbnail";
import { BackgroundSelector } from "./BackgroundSelector";

export function EntryForm({ editor: e }: { editor: Editor }) {
  const icon = e.form.icon.trim();
  const validIcon =
    e.form.type === "uncertain" ||
    (!icon && e.form.type === "group") ||
    Object.hasOwn(e.icons, icon);
  return (
    <Paper variant="outlined" sx={{ p: 2 }} component="form" onSubmit={e.save}>
      <Stack spacing={2}>
        <KeyPreview
          entry={e.form}
          parentTitle={
            e.breadcrumbs[
              e.adding ? e.breadcrumbs.length - 1 : e.breadcrumbs.length - 2
            ] || "Vogel"
          }
        />
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          Entry details
        </Typography>
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
                  required={e.form.type === "bird"}
                  error={!validIcon}
                  helperText={
                    icon
                      ? validIcon
                        ? "Icon found"
                        : "Choose an ID from data/icons.json"
                      : e.form.type === "bird"
                        ? "An icon is required for birds."
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
          </>
        )}
        <Stack direction="row" sx={{ justifyContent: "flex-end" }} spacing={1}>
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
