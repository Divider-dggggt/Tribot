import { Box, Typography } from "@mui/material";
import { ReactElement } from "react";

interface AuthLogoProps {
  subtitle: string;
}

export const AuthLogo = ({ subtitle }: AuthLogoProps): ReactElement => {
  return (
    <Box sx={{ textAlign: "center", mb: 4 }}>
      <Box
        sx={{
          width: 56,
          height: 56,
          borderRadius: "50%",
          mx: "auto",
          mb: 2,
          backgroundColor: "#7c3aed",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="22 12 18 12 15 20 10 5 7 12 2 12" />
        </svg>
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
