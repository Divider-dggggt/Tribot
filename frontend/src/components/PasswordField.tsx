import { ComponentProps, ReactElement, useState } from "react";
import { IconButton, InputAdornment } from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import { FloatingTextField } from "./FloatingTextField";

type PasswordFieldProps = Omit<ComponentProps<typeof FloatingTextField>, "type">;

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
