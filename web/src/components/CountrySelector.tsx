import { useEffect, useState } from "react";
import { Autocomplete, Box, Stack, TextField, Typography } from "@mui/material";
import { api } from "../api";

function Flag({ code }: { code: string }) {
  const query = new URLSearchParams({ code, token: location.hash.slice(1) });
  return (
    <Box
      component="img"
      src={`/api/flag-image?${query}`}
      alt=""
      loading="lazy"
      sx={{ width: 28, height: 20, objectFit: "contain", flexShrink: 0 }}
    />
  );
}

export function CountrySelector({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (code: string) => void;
  disabled: boolean;
}) {
  const [countries, setCountries] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  useEffect(() => {
    api<Record<string, string>>("/api/countries")
      .then(setCountries)
      .catch((failure: Error) => setError(failure.message));
  }, []);
  return (
    <Autocomplete
      size="small"
      options={Object.keys(countries).sort((a, b) =>
        countries[a].localeCompare(countries[b]),
      )}
      value={value || null}
      getOptionLabel={(code) => `${code} — ${countries[code] || code}`}
      onChange={(_, code) => onChange(code || "")}
      disabled={disabled}
      renderOption={(props, code) => {
        const { key, ...optionProps } = props;
        return (
          <Box component="li" key={key} {...optionProps}>
            <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
              <Flag code={code} />
              <Typography variant="body2">
                {code} — {countries[code]}
              </Typography>
            </Stack>
          </Box>
        );
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Country (optional)"
          error={!!error}
          helperText={
          error || "Adds a small flag to the bottom-left of the key."
          }
          slotProps={{
            ...params.slotProps,
            input: {
              ...params.slotProps.input,
              startAdornment: (
                <>
                  {value && <Flag code={value} />}
                  {params.slotProps.input.startAdornment}
                </>
              ),
            },
          }}
        />
      )}
    />
  );
}
