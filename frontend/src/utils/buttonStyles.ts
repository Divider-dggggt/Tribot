export const DANGER_COLORS = {
  text: "#b91c1c",
  hoverText: "#991b1b",
  hoverBackground: "#fef2f2",
  border: "#fca5a5",
  hoverBorder: "#f87171",
} as const;

export const dangerTextButtonSx = {
  color: DANGER_COLORS.text,
  "&:hover": {
    color: DANGER_COLORS.hoverText,
    backgroundColor: DANGER_COLORS.hoverBackground,
  },
} as const;

export const dangerOutlinedButtonSx = {
  color: DANGER_COLORS.text,
  borderColor: DANGER_COLORS.border,
  "&:hover": {
    color: DANGER_COLORS.hoverText,
    borderColor: DANGER_COLORS.hoverBorder,
    backgroundColor: DANGER_COLORS.hoverBackground,
  },
} as const;

export const dangerMenuItemHoverSx = {
  "&:hover": {
    color: DANGER_COLORS.text,
    backgroundColor: DANGER_COLORS.hoverBackground,
  },
} as const;
