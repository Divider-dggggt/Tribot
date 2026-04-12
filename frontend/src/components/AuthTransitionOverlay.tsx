import { ReactElement } from "react";
import { Backdrop, Box, CircularProgress, Fade, Typography } from "@mui/material";
import { keyframes } from "@mui/system";

type AuthTransitionOverlayVariant = "login" | "logout" | "expired";

interface AuthTransitionOverlayProps {
  open: boolean;
  variant: AuthTransitionOverlayVariant;
  title: string;
  subtitle: string;
}

const LoginSuccessIcon = (): ReactElement => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <circle cx="12" cy="12" r="9" />
    <path d="M8 12.5l2.5 2.5L16 9.5" />
  </svg>
);

const LogoutProgressIcon = (): ReactElement => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M10 21H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="14 7 19 12 14 17" />
    <line x1="19" y1="12" x2="9" y2="12" />
  </svg>
);

const SessionExpiredIcon = (): ReactElement => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
    <path d="m7.5 7.5 9 9" />
  </svg>
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
