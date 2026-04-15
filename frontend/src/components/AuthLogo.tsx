import { Box, Typography } from "@mui/material";
import { ReactElement } from "react";
import { BrandIcon } from "./BrandIcon";

interface AuthLogoProps {
  subtitle: string;
}

export const AuthLogo = ({ subtitle }: AuthLogoProps): ReactElement => {
  return (
    <Box sx={{ textAlign: "center", mb: 4 }}>
      <Box sx={{ mx: "auto", mb: 2, display: "flex", justifyContent: "center" }}>
        <BrandIcon size={56} iconSize={28} />
      </Box>
      <Typography
        variant="h5"
        sx={{ fontWeight: 700, letterSpacing: 0.5, color: "#111827", mb: 0.5 }}
      >
        TRIBOT
      </Typography>
      <Typography variant="body2" sx={{ color: "#6b7280" }}>
        {subtitle}
      </Typography>
    </Box>
  );
};
