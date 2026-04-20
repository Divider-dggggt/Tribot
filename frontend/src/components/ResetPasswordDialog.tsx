import { ReactElement, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import { useForm } from "react-hook-form";
import { fetchWithAuth } from "../utils/auth";
import { DANGER_COLORS } from "../utils/buttonStyles";
import { API_BASE_URL } from "../utils/constants";
import { PasswordField } from "./PasswordField";

interface ResetPasswordDialogProps {
  open: boolean;
  onClose: () => void;
  signedInEmail: string | null;
  userId: number | null;
}

interface ResetPasswordFormValues {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const defaultValues: ResetPasswordFormValues = {
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
};

const readApiError = async (response: Response): Promise<string> => {
  try {
    const body = await response.json() as { detail?: string };
    if (typeof body.detail === "string" && body.detail.trim()) {
      return body.detail;
    }
  } catch {
    // Fall back to status-based message below.
  }

  return `Request failed with status ${response.status}`;
};

export const ResetPasswordDialog = ({
  open,
  onClose,
  signedInEmail,
  userId,
}: ResetPasswordDialogProps): ReactElement => {
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setError,
    clearErrors,
    reset,
    formState: { errors, isSubmitting, submitCount },
  } = useForm<ResetPasswordFormValues>({ defaultValues });

  useEffect(() => {
    if (!open) {
      return;
    }

    reset(defaultValues);
    clearErrors();
    setFormError(null);
  }, [open, clearErrors, reset]);

  const handleClose = (): void => {
    if (isSubmitting) {
      return;
    }

    onClose();
  };

  const handleResetPassword = async (values: ResetPasswordFormValues): Promise<void> => {
    setFormError(null);

    if (signedInEmail == null || userId == null) {
      setFormError("Unable to verify your account details. Please sign in again.");
      return;
    }

    try {
      const updatePasswordResponse = await fetchWithAuth(`${API_BASE_URL}/users/${userId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          old_password: values.currentPassword,
          password: values.newPassword,
        }),
      });

      if (!updatePasswordResponse.ok) {
        const apiErrorMessage = await readApiError(updatePasswordResponse);
        if (updatePasswordResponse.status === 403 && /old password/i.test(apiErrorMessage)) {
          setError(
            "currentPassword",
            { type: "validate", message: "Current password is incorrect." },
            { shouldFocus: true }
          );
          return;
        }
        if (updatePasswordResponse.status === 400 && /same as old/i.test(apiErrorMessage)) {
          setError(
            "newPassword",
            { type: "validate", message: "New password cannot be the same as old password." },
            { shouldFocus: true }
          );
          return;
        }
        throw new Error(apiErrorMessage);
      }

      reset(defaultValues);
      onClose();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Unable to reset password right now.");
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullWidth
      maxWidth="sm"
      PaperProps={{
        sx: {
          borderRadius: 3,
          border: "1px solid #ede9fe",
          boxShadow: "0 18px 40px rgba(17, 24, 39, 0.15)",
        },
      }}
    >
      <DialogTitle sx={{ pt: 3, px: 3, pb: 1.25, fontSize: "2rem", fontWeight: 700, color: "#111827" }}>
        Reset Password
      </DialogTitle>
      <DialogContent sx={{ pt: 1, px: 3, pb: 1 }}>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2.25 }}>
          Signed in as {signedInEmail ?? "Unknown user"}
        </Typography>
        {formError && (
          <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
            {formError}
          </Alert>
        )}
        <form id="reset-password-form" onSubmit={handleSubmit(handleResetPassword)} noValidate>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <PasswordField
              fullWidth
              label="Current Password"
              required
              size="small"
              autoComplete="current-password"
              error={Boolean(errors.currentPassword)}
              helperText={errors.currentPassword?.message}
              requiredErrorSubmitCount={errors.currentPassword?.type === "required" ? submitCount : 0}
              {...register("currentPassword", {
                required: "Please enter your current password.",
              })}
            />
            <PasswordField
              fullWidth
              label="New Password"
              required
              size="small"
              autoComplete="new-password"
              error={Boolean(errors.newPassword)}
              helperText={errors.newPassword?.message}
              requiredErrorSubmitCount={errors.newPassword?.type === "required" ? submitCount : 0}
              {...register("newPassword", {
                required: "Please enter a new password.",
                minLength: {
                  value: 6,
                  message: "Password must be 6-72 characters.",
                },
                maxLength: {
                  value: 72,
                  message: "Password must be 6-72 characters.",
                },
              })}
            />
            <PasswordField
              fullWidth
              label="Confirm New Password"
              required
              size="small"
              autoComplete="new-password"
              error={Boolean(errors.confirmPassword)}
              helperText={errors.confirmPassword?.message}
              requiredErrorSubmitCount={errors.confirmPassword?.type === "required" ? submitCount : 0}
              {...register("confirmPassword", {
                required: "Please confirm your new password.",
                validate: (value, formValues) => (
                  value === formValues.newPassword || "Passwords do not match."
                ),
              })}
            />
          </Box>
        </form>
      </DialogContent>
      <DialogActions
        sx={{
          px: 3,
          pb: 3,
          pt: 1.5,
          gap: 1.5,
          flexDirection: { xs: "column-reverse", sm: "row" },
        }}
      >
        <Button
          onClick={handleClose}
          disabled={isSubmitting}
          variant="outlined"
          sx={{
            width: { xs: "100%", sm: "auto" },
            borderRadius: 2,
            py: 1.1,
            px: 2.5,
            color: "#374151",
            borderColor: "#d1d5db",
            transition: "all 160ms ease",
            "&:hover": {
              color: DANGER_COLORS.hoverText,
              borderColor: DANGER_COLORS.hoverBorder,
              backgroundColor: DANGER_COLORS.hoverBackground,
            },
          }}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          form="reset-password-form"
          variant="contained"
          disabled={isSubmitting}
          sx={{
            width: { xs: "100%", sm: "auto" },
            minWidth: { sm: 180 },
            borderRadius: 2,
            py: 1.1,
            px: 2.75,
            fontWeight: 700,
          }}
        >
          {isSubmitting ? "Updating..." : "Update Password"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
