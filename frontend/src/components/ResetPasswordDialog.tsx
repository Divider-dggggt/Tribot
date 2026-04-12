import { ReactElement, useEffect, useState } from "react";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import { useForm } from "react-hook-form";
import { fetchWithAuth } from "../utils/auth";
import { dangerTextButtonSx } from "../utils/buttonStyles";
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

    const verifyCurrentPasswordResponse = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: signedInEmail,
        password: values.currentPassword,
      }),
    });

    if (!verifyCurrentPasswordResponse.ok) {
      setError(
        "currentPassword",
        { type: "validate", message: "Current password is incorrect." },
        { shouldFocus: true }
      );
      return;
    }

    try {
      // Temporary: use self-update endpoint until dedicated password endpoint is ready.
      const updatePasswordResponse = await fetchWithAuth(`${API_BASE_URL}/users/${userId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          password: values.newPassword,
        }),
      });

      if (!updatePasswordResponse.ok) {
        throw new Error(await readApiError(updatePasswordResponse));
      }

      reset(defaultValues);
      onClose();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Unable to reset password right now.");
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="xs">
      <DialogTitle>Reset Password</DialogTitle>
      <DialogContent sx={{ pt: 1 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Signed in as {signedInEmail ?? "Unknown user"}
        </Typography>
        {formError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}
        <form id="reset-password-form" onSubmit={handleSubmit(handleResetPassword)} noValidate>
          <PasswordField
            fullWidth
            label="Current Password"
            required
            size="small"
            sx={{ mb: 2 }}
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
            sx={{ mb: 2 }}
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
        </form>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2.5 }}>
        <Button
          onClick={handleClose}
          disabled={isSubmitting}
          sx={dangerTextButtonSx}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          form="reset-password-form"
          variant="contained"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Updating..." : "Update Password"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
