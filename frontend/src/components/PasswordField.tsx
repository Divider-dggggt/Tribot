import { ReactElement, useState } from "react";
import { IconButton, InputAdornment, SvgIcon, TextFieldProps } from "@mui/material";
import { FloatingTextField } from "./FloatingTextField";

type PasswordFieldProps = Omit<TextFieldProps, "type">;

const VisibilityIcon = (): ReactElement => (
  <SvgIcon fontSize="small" viewBox="0 0 24 24">
    <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zm0 12.5c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
  </SvgIcon>
);

const VisibilityOffIcon = (): ReactElement => (
  <SvgIcon fontSize="small" viewBox="0 0 24 24">
    <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92C21.29 15.26 22.6 13.73 23 12c-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2.81 2.81 1.54 4.08l3.38 3.38C3.12 8.74 1.71 10.27 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l3.54 3.54 1.27-1.27L2.81 2.81zM12 17c-2.76 0-5-2.24-5-5 0-.65.13-1.26.36-1.83l1.53 1.53A2.996 2.996 0 0 0 12 15c.85 0 1.62-.35 2.17-.91l1.53 1.53c-.57.23-1.18.38-1.83.38zm0-8c1.66 0 3 1.34 3 3 0 .35-.06.69-.17 1l-3.83-3.83c.31-.11.65-.17 1-.17z" />
  </SvgIcon>
);

export const PasswordField = ({ InputProps, ...restProps }: PasswordFieldProps): ReactElement => {
  const [isVisible, setIsVisible] = useState<boolean>(false);

  return (
    <FloatingTextField
      {...restProps}
      type={isVisible ? "text" : "password"}
      InputProps={{
        ...InputProps,
        endAdornment: (
          <>
            {InputProps?.endAdornment}
            <InputAdornment position="end">
              <IconButton
                edge="end"
                onClick={() => setIsVisible((previous) => !previous)}
                onMouseDown={(event) => event.preventDefault()}
                aria-label={isVisible ? "Hide password" : "Show password"}
                size="small"
              >
                {isVisible ? <VisibilityOffIcon /> : <VisibilityIcon />}
              </IconButton>
            </InputAdornment>
          </>
        ),
      }}
    />
  );
};
