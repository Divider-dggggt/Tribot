import { createTheme } from "@mui/material/styles";

const brandPurple = {
  main: "#9333ea",
  dark: "#7e22ce",
  text: "#7c3aed",
  hoverText: "#6d28d9",
  hoverBg: "#f5f3ff",
  selectedBg: "#f3e8ff",
  selectedHoverBg: "#ede9fe",
};

export const appTheme = createTheme({
  palette: {
    primary: {
      main: brandPurple.main,
      dark: brandPurple.dark,
    },
  },
  components: {
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          textTransform: "none",
        },
        text: {
          "&:hover": {
            color: brandPurple.hoverText,
            backgroundColor: brandPurple.hoverBg,
          },
        },
        textInherit: {
          color: "#374151",
          "&:hover": {
            color: brandPurple.hoverText,
            backgroundColor: brandPurple.hoverBg,
          },
        },
      },
      variants: [
        {
          props: { variant: "contained" },
          style: {
            backgroundColor: brandPurple.main,
            "&:hover": {
              backgroundColor: brandPurple.dark,
            },
          },
        },
        {
          props: { variant: "outlined" },
          style: {
            color: brandPurple.text,
            borderColor: "#c4b5fd",
            "&:hover": {
              color: brandPurple.hoverText,
              borderColor: "#a78bfa",
              backgroundColor: brandPurple.hoverBg,
            },
          },
        },
      ],
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 600,
          color: "#6b7280",
          "&:hover": {
            color: brandPurple.hoverText,
            backgroundColor: brandPurple.hoverBg,
          },
          "&.Mui-selected": {
            color: brandPurple.text,
            backgroundColor: brandPurple.selectedBg,
            "&:hover": {
              backgroundColor: brandPurple.selectedHoverBg,
            },
          },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          "&:hover": {
            color: brandPurple.text,
            backgroundColor: brandPurple.hoverBg,
          },
          "&:hover .MuiListItemIcon-root": {
            color: brandPurple.text,
          },
          "&.Mui-selected": {
            color: brandPurple.text,
            backgroundColor: brandPurple.selectedBg,
            "&:hover": {
              backgroundColor: brandPurple.selectedBg,
            },
          },
          "&.Mui-selected .MuiListItemIcon-root": {
            color: brandPurple.text,
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          "&:hover": {
            color: brandPurple.hoverText,
            backgroundColor: brandPurple.hoverBg,
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          "&.MuiTableRow-hover:hover": {
            backgroundColor: brandPurple.hoverBg,
          },
          "&.MuiTableRow-hover:hover > *": {
            backgroundColor: brandPurple.hoverBg,
          },
        },
      },
    },
  },
});
