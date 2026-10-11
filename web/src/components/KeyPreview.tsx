import { useEffect, useState } from "react";
import { Alert, Box, CircularProgress, Stack, Typography } from "@mui/material";
import type { EntryForm } from "../types";
import { displayName } from "../displayName";

export function KeyPreview({
  entry,
  parentTitle,
}: {
  entry: EntryForm;
  parentTitle: string;
}) {
  const [image, setImage] = useState<string>();
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [titleSettings, setTitleSettings] = useState<{
    Title: string;
    TitleAlignment: "top" | "middle" | "bottom";
    FontSize: number;
    TitleColor: string;
    OutlineThickness: number;
  }>();
  const title = titleSettings?.Title || "";

  useEffect(() => {
    const controller = new AbortController();
    let objectUrl: string | undefined;
    setImage(undefined);
    setError(undefined);
    setLoading(true);
    const timer = window.setTimeout(async () => {
      try {
        const response = await fetch(
          "/api/preview",
          {
            method: "POST",
            headers: {
              "X-BirdDeck-Token": location.hash.slice(1),
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ entry, parentTitle }),
            signal: controller.signal,
          },
        );
        if (!response.ok)
          throw new Error((await response.json()).error || "Preview failed");
        const blob = await response.blob();
        if (controller.signal.aborted) return;
        objectUrl = URL.createObjectURL(blob);
        setTitleSettings(
          JSON.parse(response.headers.get("X-BirdDeck-Title") || "{}"),
        );
        setImage(objectUrl);
      } catch (failure) {
        if (!controller.signal.aborted)
          setError(
            failure instanceof Error ? failure.message : "Preview failed",
          );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 250);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [entry, parentTitle]);

  return (
    <Stack spacing={1} sx={{ alignItems: "flex-start" }}>
      <Typography variant="subtitle2">
        Key preview
      </Typography>
      <Box
        sx={{
          width: 160,
          height: 160,
          position: "relative",
          bgcolor: "common.black",
          borderRadius: "26px",
          border: "8px solid black",
          overflow: "hidden",
          display: "grid",
          placeItems: "center",
        }}
      >
        {image && (
          <Box
            component="img"
            src={image}
            alt={`Key image for ${displayName(entry.title || parentTitle || "new entry")}`}
            sx={{ width: "100%", height: "100%" }}
          />
        )}
        {loading && <CircularProgress size={24} />}
        {image && (
          <Typography
            sx={{
              position: "absolute",
              top:
                titleSettings?.TitleAlignment === "top"
                  ? 6
                  : titleSettings?.TitleAlignment === "middle"
                    ? "50%"
                    : undefined,
              bottom:
                titleSettings?.TitleAlignment === "bottom" ? 6 : undefined,
              transform:
                titleSettings?.TitleAlignment === "middle"
                  ? "translateY(-50%)"
                  : undefined,
              whiteSpace: "pre-wrap",
              left: titleSettings?.TitleAlignment === "top" ? 24 : 4,
              right: 4,
              textAlign: "center",
              color: titleSettings?.TitleColor || "#ffffff",
              fontSize: (titleSettings?.FontSize || 9) * 2,
              fontFamily: "Arial, sans-serif",
              WebkitTextStroke: "1px black",
              paintOrder: "stroke fill",
              lineHeight: 1.2,
              textShadow: "0 1px 3px black, 0 0 3px black",
              overflowWrap: "anywhere",
            }}
          >
            {title}
          </Typography>
        )}
      </Box>
      {error && (
        <Alert severity="warning" sx={{ py: 0 }}>
          {error}
        </Alert>
      )}
    </Stack>
  );
}
