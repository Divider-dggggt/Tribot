import { ReactElement } from "react";
import { Backdrop, Box, CircularProgress, Fade, Typography } from "@mui/material";
import { keyframes } from "@mui/system";
import TaskAltRoundedIcon from "@mui/icons-material/TaskAltRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import TimerOffOutlinedIcon from "@mui/icons-material/TimerOffOutlined";

type AuthTransitionOverlayVariant = "login" | "logout" | "expired";

interface AuthTransitionOverlayProps {
  open: boolean;
  variant: AuthTransitionOverlayVariant;
  title: string;
  subtitle: string;
}

const LoginSuccessIcon = (): ReactElement => (
  <TaskAltRoundedIcon sx={{ fontSize: 28 }} aria-hidden />
);

const LogoutProgressIcon = (): ReactElement => (
  <LogoutRoundedIcon sx={{ fontSize: 24 }} aria-hidden />
);

const SessionExpiredIcon = (): ReactElement => (
  <TimerOffOutlinedIcon sx={{ fontSize: 28 }} aria-hidden />
);

const panelEnter = keyframes`
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
`;

const iconPulse = keyframes`
  0% {
    box-shadow: 0 0 0 0 rgba(124, 58, 237, 0.28);
  }
  100% {
    box-shadow: 0 0 0 16px rgba(124, 58, 237, 0);
  }
`;

/**
 * A transition overlay detailing any authentication in action.
 * @param {Object} props The component props.
 * @param {boolean} props.open Whether the overlay is open.
 * @param {AuthTransitionOverlayVariant} props.variant What type of authentication action is actioned.
 * @param {string} props.title The title displayed when the overlay is open.
 * @param {string} props.subtitle The subtitle displayed when the overlay is open.
 * @returns {JSX.Element} An authentication transition overlay element.
 */
export const AuthTransitionOverlay = ({
  open,
  variant,
  title,
  subtitle,
}: AuthTransitionOverlayProps): ReactElement => {
  const isLogout = variant === "logout";
  const isExpired = variant === "expired";

  return (
    <Backdrop
      open={open}
      sx={{
        zIndex: (theme) => theme.zIndex.modal + 10,
        bgcolor: "rgba(15, 23, 42, 0.42)",
        backdropFilter: "blur(2px)",
      }}
    >
      <Fade in={open} timeout={{ enter: 220, exit: 120 }}>
        <Box
          sx={{
            width: "min(90vw, 320px)",
            borderRadius: 3,
            px: 3,
            py: 3.5,
            textAlign: "center",
            bgcolor: "#fff",
            boxShadow: "0 18px 45px rgba(15, 23, 42, 0.24)",
            animation: `${panelEnter} 220ms ease-out`,
          }}
        >
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              mx: "auto",
              mb: 1.6,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              position: "relative",
              bgcolor: isLogout
                ? "rgba(124, 58, 237, 0.08)"
                : isExpired
                  ? "rgba(245, 158, 11, 0.16)"
                  : "rgba(16, 185, 129, 0.12)",
              color: isLogout ? "#7c3aed" : isExpired ? "#b45309" : "#059669",
              animation: `${iconPulse} 1s ease-out infinite`,
            }}
          >
            {isLogout ? (
              <>
                <CircularProgress size={56} thickness={4} />
                <Box
                  sx={{
                    position: "absolute",
                    width: 30,
                    height: 30,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    bgcolor: "#fff",
                    borderRadius: "50%",
                  }}
                >
                  <LogoutProgressIcon />
                </Box>
              </>
            ) : isExpired ? (
              <SessionExpiredIcon />
            ) : (
              <LoginSuccessIcon />
            )}
          </Box>
          <Typography sx={{ color: "#111827", fontWeight: 700 }}>{title}</Typography>
          <Typography sx={{ color: "#6b7280", mt: 0.6, fontSize: "0.95rem" }}>{subtitle}</Typography>
        </Box>
      </Fade>
    </Backdrop>
  );
};
