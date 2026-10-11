import { useEffect, useState } from "react";
import {
  Autocomplete,
  Box,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { api } from "../api";
import { ImageThumbnail } from "./ImageThumbnail";

export function BackgroundSelector({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}) {
  const [files, setFiles] = useState<string[]>([]);
  const [error, setError] = useState("");
  const mode = !value || value.startsWith("#") ? "color" : "image";

  useEffect(() => {
    api<string[]>("/api/backgrounds")
      .then(setFiles)
      .catch((failure: Error) => setError(failure.message));
  }, []);

  const color = /^#[\da-f]{6}$/i.test(value)
    ? value
    : /^#[\da-f]{3}$/i.test(value)
      ? "#" +
        value
          .slice(1)
          .split("")
          .map((part) => part + part)
          .join("")
      : "#ffffff";
  return (
    <Stack spacing={2}>
      <TextField
        select
        size="small"
        label="Background type"
        value={mode}
        disabled={disabled}
        onChange={(event) =>
          onChange(
            event.target.value === "color"
              ? "#ffffff"
              : files[0] || "assets/img/unknown-bird.png",
          )
        }
      >
        <MenuItem value="color">Color</MenuItem>
        <MenuItem value="image" disabled={!files.length}>
          Local image
        </MenuItem>
      </TextField>
      {mode === "color" ? (
        <TextField
          sx={{ width: 140 }}
          size="small"
          type="color"
          label="Background color"
          value={color}
          disabled={disabled}
          onChange={(event) => onChange(event.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
        />
      ) : (
        <Autocomplete
          size="small"
          value={value}
          disabled={disabled}
          disableClearable
          options={Array.from(new Set([...files, value]))}
          getOptionLabel={(file) => file.split("/").pop() || file}
          onChange={(_, file, reason) => {
            if (reason === "selectOption") onChange(file);
          }}
          renderOption={(props, file) => {
            const { key, ...optionProps } = props;
            return (
              <Box component="li" key={key} {...optionProps}>
                <Stack
                  direction="row"
                  spacing={1.5}
                  sx={{ alignItems: "center" }}
                >
                  <ImageThumbnail kind="background" value={file} />
                  <Typography variant="body2">
                    {file.split("/").pop()}
                  </Typography>
                </Stack>
              </Box>
            );
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label="Background image"
              slotProps={{
                ...params.slotProps,
                input: {
                  ...params.slotProps.input,
                  startAdornment: (
                    <>
                      <ImageThumbnail
                        kind="background"
                        value={value}
                        size={24}
                      />
                      {params.slotProps.input.startAdornment}
                    </>
                  ),
                },
              }}
            />
          )}
        />
      )}
      {error && (
        <Typography color="error" variant="caption">
          {error}
        </Typography>
      )}
    </Stack>
  );
}
