import { ReactElement } from "react";
import { TextField, TextFieldProps } from "@mui/material";
import { SxProps, Theme } from "@mui/material/styles";

const baseInputSx: SxProps<Theme> = {
  borderRadius: 2,
  bgcolor: "#fff",
};

const requiredAsteriskSx: SxProps<Theme> = {
  "& .MuiInputLabel-asterisk": {
    color: "#dc2626",
  },
};

const mergeSx = (baseSx: SxProps<Theme>, customSx?: SxProps<Theme>): SxProps<Theme> => (
  customSx == null ? baseSx : [baseSx, customSx]
);

export const FloatingTextField = ({
  fullWidth = true,
  size = "small",
  variant = "outlined",
  required = false,
  InputProps,
  sx,
  ...restProps
}: TextFieldProps): ReactElement => (
  <TextField
    {...restProps}
    fullWidth={fullWidth}
    size={size}
    variant={variant}
    required={required}
    sx={required ? mergeSx(requiredAsteriskSx, sx) : sx}
    InputProps={{
      ...InputProps,
      sx: mergeSx(baseInputSx, InputProps?.sx),
    }}
  />
);
