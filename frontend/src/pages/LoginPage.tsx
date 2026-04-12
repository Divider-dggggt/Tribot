import { ReactElement, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
} from "@mui/material";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { AuthLogo } from "../components/AuthLogo";
import { AuthTransitionOverlay } from "../components/AuthTransitionOverlay";
import { FloatingTextField } from "../components/FloatingTextField";
import { PasswordField } from "../components/PasswordField";
import { consumeSessionExpiredTransition } from "../utils/auth";
import { API_BASE_URL } from "../utils/constants";

interface LoginResponse {
  access_token: string;
  token_type: string;
  role: string;
}

interface LoginFormValues {
  email: string;
  password: string;
}

const LOGIN_NAVIGATION_DELAY_MS = 600;
const SESSION_EXPIRED_NOTICE_DELAY_MS = 900;

const readLoginError = async (response: Response): Promise<string> => {
  try {
    const body = await response.json() as { detail?: string };
    if (typeof body.detail === "string" && body.detail.trim()) {
      return body.detail;
    }
  } catch {
    // Fallback below.
  }

  return `Login failed with status ${response.status}`;
};

export const LoginPage = (): ReactElement => {
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoginTransitioning, setIsLoginTransitioning] = useState<boolean>(false);
  const [isSessionExpiredTransitioning, setIsSessionExpiredTransitioning] = useState<boolean>(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    defaultValues: {
      email: "",
      password: "",
    },
  });

  useEffect(() => {
    if (!consumeSessionExpiredTransition()) {
      return;
    }

    setIsSessionExpiredTransitioning(true);
    const timer = window.setTimeout(() => {
      setIsSessionExpiredTransitioning(false);
    }, SESSION_EXPIRED_NOTICE_DELAY_MS);

    return () => {
      window.clearTimeout(timer);
    };
  }, []);

  const isInteractionBlocked = isSubmitting || isLoginTransitioning || isSessionExpiredTransitioning;

  const handleSignIn = async (values: LoginFormValues): Promise<void> => {
    setErrorMessage(null);
    const trimmedEmail = values.email.trim();

    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: trimmedEmail,
          password: values.password,
        }),
      });

      if (!response.ok) {
        throw new Error(await readLoginError(response));
      }

      const data = await response.json() as LoginResponse;
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("token_type", data.token_type);
      localStorage.setItem("user_role", data.role);
      localStorage.setItem("user_email", trimmedEmail);

      setIsLoginTransitioning(true);
      await new Promise<void>((resolve) => {
        window.setTimeout(resolve, LOGIN_NAVIGATION_DELAY_MS);
      });
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setIsLoginTransitioning(false);
      setErrorMessage(error instanceof Error ? error.message : "Unable to sign in right now.");
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: "#f3edf9",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        px: 2,
      }}
    >
      <Card
        elevation={0}
        sx={{
          width: "100%",
          maxWidth: 420,
          borderRadius: 3,
          border: "1px solid #ede9fe",
          boxShadow: "0 16px 40px rgba(17, 24, 39, 0.16)",
        }}
      >
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <AuthLogo subtitle="Clinician Triage System" />

          <Box component="form" onSubmit={handleSubmit(handleSignIn)} noValidate>
            {errorMessage && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {errorMessage}
              </Alert>
            )}
            <FloatingTextField
              fullWidth
              type="email"
              label="Email"
              required
              placeholder="Enter your email"
              size="small"
              sx={{ mb: 2.5 }}
              disabled={isInteractionBlocked}
              error={Boolean(errors.email)}
              helperText={errors.email?.message}
              {...register("email", {
                required: "Please enter your email.",
                setValueAs: (value: string) => value.trim(),
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: "Please enter a valid email address.",
                },
              })}
            />
            <PasswordField
              fullWidth
              label="Password"
              required
              placeholder="Enter your password"
              size="small"
              sx={{ mb: 2.5 }}
              disabled={isInteractionBlocked}
              error={Boolean(errors.password)}
              helperText={errors.password?.message}
              {...register("password", {
                required: "Please enter your password.",
              })}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={isInteractionBlocked}
              sx={{
                borderRadius: 2,
                py: 1.2,
                fontWeight: 600,
                fontSize: "1rem",
              }}
            >
              {isInteractionBlocked ? (
                <CircularProgress size={20} color="inherit" sx={{ mr: 1 }} />
              ) : null}
              {isSessionExpiredTransitioning
                ? "Session expired"
                : isLoginTransitioning
                  ? "Preparing workspace..."
                  : isSubmitting
                    ? "Signing In..."
                    : "Sign In"}
            </Button>
          </Box>
        </CardContent>
      </Card>
      <AuthTransitionOverlay
        open={isSessionExpiredTransitioning}
        variant="expired"
        title="Session expired"
        subtitle="Please sign in again."
      />
      <AuthTransitionOverlay
        open={isLoginTransitioning}
        variant="login"
        title="Login successful"
        subtitle="Taking you to the dashboard..."
      />
    </Box>
  );
};
