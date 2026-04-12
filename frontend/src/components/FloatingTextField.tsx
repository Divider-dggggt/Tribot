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

const requiredFieldShakeSx = (submitCount: number): SxProps<Theme> => {
  const animationName = submitCount % 2 === 0 ? "requiredFieldShakeEven" : "requiredFieldShakeOdd";

  return {
    "@keyframes requiredFieldShakeOdd": {
      "10%, 90%": { transform: "translate3d(-1px, 0, 0)" },
      "20%, 80%": { transform: "translate3d(2px, 0, 0)" },
      "30%, 50%, 70%": { transform: "translate3d(-4px, 0, 0)" },
      "40%, 60%": { transform: "translate3d(4px, 0, 0)" },
    },
    "@keyframes requiredFieldShakeEven": {
      "10%, 90%": { transform: "translate3d(-1px, 0, 0)" },
      "20%, 80%": { transform: "translate3d(2px, 0, 0)" },
      "30%, 50%, 70%": { transform: "translate3d(-4px, 0, 0)" },
      "40%, 60%": { transform: "translate3d(4px, 0, 0)" },
    },
    "& .MuiOutlinedInput-root": {
      animationName,
      animationDuration: "320ms",
      animationTimingFunction: "cubic-bezier(.36,.07,.19,.97)",
    },
  };
};

const mergeSx = (baseSx: SxProps<Theme>, customSx?: SxProps<Theme>): SxProps<Theme> => (
  customSx == null ? baseSx : [baseSx, customSx] as SxProps<Theme>
);

type FloatingTextFieldProps = TextFieldProps & {
  requiredErrorSubmitCount?: number;
};

export const FloatingTextField = ({
  fullWidth = true,
  size = "small",
  variant = "outlined",
  required = false,
  requiredErrorSubmitCount = 0,
  InputProps,
  sx,
  ...restProps
}: FloatingTextFieldProps): ReactElement => {
  const withRequiredAsteriskSx = required ? mergeSx(requiredAsteriskSx, sx) : sx;
  const mergedSx = requiredErrorSubmitCount > 0
    ? mergeSx(requiredFieldShakeSx(requiredErrorSubmitCount), withRequiredAsteriskSx)
    : withRequiredAsteriskSx;

  return (
    <TextField
      {...restProps}
      fullWidth={fullWidth}
      size={size}
      variant={variant}
      required={required}
      sx={mergedSx}
      InputProps={{
        ...InputProps,
        sx: mergeSx(baseInputSx, InputProps?.sx),
      }}
    />
  );
};
