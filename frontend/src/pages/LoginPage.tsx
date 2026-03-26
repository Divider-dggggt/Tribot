import { ReactElement, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  TextField,
  Typography,
} from "@mui/material";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { AuthLogo } from "../components/AuthLogo";
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

      navigate("/dashboard", { replace: true });
    } catch (error) {
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
            <Typography variant="subtitle2" sx={{ color: "#374151", mb: 0.75 }}>
              Email
            </Typography>
            <TextField
              fullWidth
              type="email"
              placeholder="Enter your email"
              size="small"
              sx={{ mb: 2.5 }}
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
              InputProps={{
                sx: {
                  borderRadius: 2,
                  backgroundColor: "#fff",
                },
              }}
            />

            <Typography variant="subtitle2" sx={{ color: "#374151", mb: 0.75 }}>
              Password
            </Typography>
            <TextField
              fullWidth
              type="password"
              placeholder="Enter your password"
              size="small"
              sx={{ mb: 2.5 }}
              error={Boolean(errors.password)}
              helperText={errors.password?.message}
              {...register("password", {
                required: "Please enter your password.",
              })}
              InputProps={{
                sx: {
                  borderRadius: 2,
                  backgroundColor: "#fff",
                },
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={isSubmitting}
              sx={{
                textTransform: "none",
                borderRadius: 2,
                py: 1.2,
                fontWeight: 600,
                fontSize: "1rem",
                bgcolor: "#9333ea",
                "&:hover": {
                  bgcolor: "#7e22ce",
                },
              }}
            >
              {isSubmitting ? (
                <CircularProgress size={20} color="inherit" sx={{ mr: 1 }} />
              ) : null}
              {isSubmitting ? "Signing In..." : "Sign In"}
            </Button>

            <Button
              type="button"
              fullWidth
              variant="outlined"
              onClick={() => navigate("/create-account")}
              sx={{
                textTransform: "none",
                borderRadius: 2,
                mt: 2.5,
                py: 1.2,
                fontSize: "1rem",
                fontWeight: 500,
                color: "#9333ea",
                borderColor: "#9333ea",
                "&:hover": {
                  borderColor: "#7e22ce",
                  backgroundColor: "#faf5ff",
                },
              }}
            >
              Create New Account
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};
