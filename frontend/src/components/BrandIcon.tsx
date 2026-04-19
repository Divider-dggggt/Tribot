import { ReactElement } from "react";
import { Box } from "@mui/material";
import MonitorHeartOutlinedIcon from "@mui/icons-material/MonitorHeartOutlined";

interface BrandIconProps {
  size?: number;
  iconSize?: number;
}

export const BrandIcon = ({ size = 56, iconSize = 28 }: BrandIconProps): ReactElement => {
  return (
    <Box
      sx={{
        width: size,
        height: size,
        borderRadius: "50%",
        backgroundColor: "#7c3aed",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <MonitorHeartOutlinedIcon sx={{ color: "white", fontSize: iconSize }} />
    </Box>
  );
};
