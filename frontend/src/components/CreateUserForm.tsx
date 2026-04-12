import { ReactElement, useMemo } from "react";
import { Box, Button, Dialog, DialogContent, Grid, Stack, Typography } from "@mui/material";
import { Controller, useForm } from "react-hook-form";
import { AuthLogo } from "./AuthLogo";
import { FloatingTextField } from "./FloatingTextField";
import { PasswordField } from "./PasswordField";
import { UserRole } from "../types/user";
import { dangerOutlinedButtonSx } from "../utils/buttonStyles";
import { API_BASE_URL } from "../utils/constants";
import { fetchWithAuth } from "../utils/auth";

const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  [UserRole.Admin]: [
    "View all patient records",
    "Access evaluation tools",
    "Generate reports",
    "Administrative access",
  ],
  [UserRole.Clinician]: [
    "Create new cases",
    "Override AI predictions",
    "Access evaluation tools",
  ],
  [UserRole.Researcher]: [
    "Generate reports",
    "View all patient records",
    "Access evaluation tools",
  ],
};

const ROLE_BUTTON_COLORS: Record<UserRole, { text: string; bg: string; border: string }> = {
  [UserRole.Admin]: {
    text: "#6d28d9",
    bg: "#ede9fe",
    border: "#c4b5fd",
  },
  [UserRole.Clinician]: {
    text: "#166534",
    bg: "#dcfce7",
    border: "#86efac",
  },
  [UserRole.Researcher]: {
    text: "#0c4a6e",
    bg: "#e0f2fe",
    border: "#7dd3fc",
  },
};

const readCreateUserError = async (response: Response): Promise<string> => {
  try {
    const body = await response.json() as { detail?: string };
    if (typeof body.detail === "string" && body.detail.trim()) {
      return body.detail;
    }
  } catch {
    // Fall back to status-based message below.
  }

  return `Create user failed with status ${response.status}`;
};

const isDuplicateEmailError = (message: string): boolean => (
  /email/i.test(message) && /(duplicate key value|already exists|unique constraint)/i.test(message)
);

interface CreateUserFormValues {
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
  password: string;
  confirmPassword: string;
}

interface CreateUserFormProps {
  open: boolean;
  onClose: () => void;
}

export const CreateUserForm = ({ open, onClose }: CreateUserFormProps): ReactElement => {
  const defaultValues: CreateUserFormValues = {
    firstName: "",
    lastName: "",
    email: "",
    role: UserRole.Clinician,
    password: "",
    confirmPassword: "",
  };
  const {
    register,
    control,
    handleSubmit,
    reset,
    clearErrors,
    setError,
    watch,
    formState: { errors },
  } = useForm<CreateUserFormValues>({
    defaultValues,
  });
  const passwordValue = watch("password", "");
  const selectedRole = watch("role", defaultValues.role);
  const permissionColumns = useMemo(() => {
    const permissions = ROLE_PERMISSIONS[selectedRole] ?? [];
    const midpoint = Math.ceil(permissions.length / 2);
    return [permissions.slice(0, midpoint), permissions.slice(midpoint)];
  }, [selectedRole]);

  const handleCreate = async (values: CreateUserFormValues): Promise<void> => {
    clearErrors("email");

    const response = await fetchWithAuth(`${API_BASE_URL}/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: `${values.firstName} ${values.lastName}`,
        email: values.email.trim(),
        role: values.role,
        password: values.password,
      }),
    });

    if (!response.ok) {
      const errorMessage = await readCreateUserError(response);
      if (isDuplicateEmailError(errorMessage)) {
        setError(
          "email",
          { type: "server", message: "An account with this email already exists" },
          { shouldFocus: true }
        );
        return;
      }
      setError(
        "email",
        { type: "server", message: "Unable to create user. Please try again." },
        { shouldFocus: true }
      );
      return;
    }

    handleReset();
    onClose();
  };

  const handleReset = () => {
    reset(defaultValues);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      disablePortal
      scroll="body"
      fullWidth
      maxWidth="md"
      PaperProps={{
        sx: {
          width: "min(900px, calc(100% - 32px))",
          maxWidth: "900px",
        },
      }}
    >
      <DialogContent
        sx={{
          width: "100%",
          borderRadius: 3,
          border: "1px solid #ede9fe",
          boxShadow: "0 18px 40px rgba(17, 24, 39, 0.15)",
        }}
      >
        <AuthLogo subtitle="Create New User" />

        <Box component="form" onSubmit={handleSubmit(handleCreate)} noValidate>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FloatingTextField
                fullWidth
                label="First Name"
                required
                placeholder="Enter first name"
                size="small"
                error={Boolean(errors.firstName)}
                helperText={errors.firstName?.message}
                {...register("firstName", { required: "Required" })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FloatingTextField
                fullWidth
                label="Last Name"
                required
                placeholder="Enter last name"
                size="small"
                error={Boolean(errors.lastName)}
                helperText={errors.lastName?.message}
                {...register("lastName", { required: "Required" })}
              />
            </Grid>
          </Grid>
          <FloatingTextField
            fullWidth
            label="Email Address"
            required
            placeholder="email@example.com"
            size="small"
            sx={{ mt: 2 }}
            error={Boolean(errors.email)}
            helperText={errors.email?.message}
            {...register("email", {
              required: "Required",
              setValueAs: (value: string) => value.trim(),
              onChange: () => clearErrors("email"),
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: "Enter a valid email address",
              },
            })}
          />
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <PasswordField
                fullWidth
                label="Temporary Password"
                required
                placeholder="Enter password (6-72 characters)"
                size="small"
                autoComplete="new-password"
                sx={{ mt: 2 }}
                error={Boolean(errors.password)}
                helperText={errors.password?.message}
                {...register("password", {
                  required: "Required",
                  minLength: {
                    value: 6,
                    message: "Password must be 6-72 characters",
                  },
                  maxLength: {
                    value: 72,
                    message: "Password must be 6-72 characters",
                  },
                })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <PasswordField
                fullWidth
                label="Confirm Password"
                required
                placeholder="Confirm password"
                size="small"
                autoComplete="new-password"
                sx={{ mt: 2 }}
                error={Boolean(errors.confirmPassword)}
                helperText={errors.confirmPassword?.message}
                {...register("confirmPassword", {
                  required: "Required",
                  validate: (value) => value === passwordValue || "Passwords do not match",
                })}
              />
            </Grid>
          </Grid>

          <Typography variant="subtitle2" sx={{ mb: 0.75, mt: 2, color: "#374151", fontWeight: 600 }}>
            User Role
            <Box component="span" sx={{ color: "#dc2626", ml: 0.5 }}>
              *
            </Box>
          </Typography>
          <Controller
            name="role"
            control={control}
            rules={{ required: "Required" }}
            render={({ field }) => (
              <>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mb: 0.75 }}>
                  {Object.values(UserRole).map((role) => {
                    const isSelected = role === field.value;
                    const roleColors = ROLE_BUTTON_COLORS[role];
                    return (
                      <Button
                        key={role}
                        type="button"
                        variant="outlined"
                        onClick={() => field.onChange(role)}
                        sx={{
                          flex: 1,
                          borderRadius: 2,
                          textTransform: "none",
                          py: 1.1,
                          transition: "all 160ms ease",
                          color: isSelected ? roleColors.text : "#374151",
                          borderColor: isSelected ? roleColors.border : "#d1d5db",
                          backgroundColor: isSelected ? roleColors.bg : "#fff",
                          "&:hover": {
                            color: roleColors.text,
                            borderColor: roleColors.border,
                            backgroundColor: roleColors.bg,
                          },
                        }}
                      >
                        {role}
                      </Button>
                    );
                  })}
                </Stack>
                {errors.role?.message ? (
                  <Typography variant="caption" sx={{ color: "#dc2626", mb: 2.5, display: "block" }}>
                    {errors.role.message}
                  </Typography>
                ) : (
                  <Box sx={{ mb: 2.5 }} />
                )}
              </>
            )}
          />

          <Typography variant="h6" sx={{ mt: 4, mb: 1.5, fontSize: "1.1rem", fontWeight: 700 }}>
            System Permissions
          </Typography>

          <Box
            sx={{
              borderRadius: 1.5,
              bgcolor: "#f3f4f6",
              p: 2,
              mb: 3,
            }}
          >
            <Grid container spacing={2}>
              {permissionColumns.map((column, index) => (
                <Grid key={index} size={{ xs: 12, md: 6 }}>
                  <Stack spacing={0.75}>
                    {column.map((permission) => (
                      <Typography key={permission} variant="body2" sx={{ color: "#374151" }}>
                        {permission}
                      </Typography>
                    ))}
                  </Stack>
                </Grid>
              ))}
            </Grid>
          </Box>

          <Stack spacing={1.5}>
            <Button
              type="submit"
              variant="contained"
              fullWidth
              sx={{
                borderRadius: 2,
                py: 1.25,
                fontWeight: 600,
                fontSize: "1.05rem",
              }}
            >
              Create User
            </Button>

            <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
              <Button
                type="button"
                variant="outlined"
                onClick={handleReset}
                fullWidth
                sx={{
                  borderRadius: 2,
                  py: 1.15,
                  color: "#374151",
                  borderColor: "#d1d5db",
                }}
              >
                Reset Form
              </Button>
              <Button
                type="button"
                variant="outlined"
                onClick={onClose}
                fullWidth
                sx={{
                  borderRadius: 2,
                  py: 1.15,
                  ...dangerOutlinedButtonSx,
                }}
              >
                Cancel
              </Button>
            </Stack>
          </Stack>
        </Box>
      </DialogContent>
    </Dialog>
  );
};
