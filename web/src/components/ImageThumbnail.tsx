import { Box } from "@mui/material";

export function imageUrl(kind: "icon" | "background", value: string) {
  const query = new URLSearchParams({
    token: location.hash.slice(1),
    [kind === "icon" ? "id" : "path"]: value,
  });
  return `/api/${kind}-image?${query}`;
}

export function ImageThumbnail({
  kind,
  value,
  size = 40,
}: {
  kind: "icon" | "background";
  value: string;
  size?: number;
}) {
  return (
    <Box
      component="img"
      src={imageUrl(kind, value)}
      alt=""
      loading="lazy"
      sx={{
        width: size,
        height: size,
        objectFit: "contain",
        flexShrink: 0,
        borderRadius: 1,
      }}
    />
  );
}
