import { ReactElement, useEffect, useMemo, useState } from "react";
import { Box, Button, CircularProgress, Dialog, DialogContent, Grid, Stack, Typography } from "@mui/material";
import { Controller, useForm } from "react-hook-form";
import { AuthLogo } from "./AuthLogo";
import { FloatingTextField } from "./FloatingTextField";
import { PasswordField } from "./PasswordField";
import { User, UserRole } from "../types/user";
import { API_BASE_URL, ROLE_PERMISSIONS } from "../utils/constants";
import { fetchWithAuth, getDecodedToken } from "../utils/auth";

interface EditUserFormValues {
  name: string;
  email: string;
  role: UserRole;
  password: string;
  confirmPassword: string;
}

interface EditUserFormProps {
  userId?: number;
  onClose: () => void;
}

export const EditUserForm = ({ userId, onClose }: EditUserFormProps): ReactElement => {
  const open = userId != null;
  const selfUserId = getDecodedToken()?.user_id;
  const isEditingSelf = userId === selfUserId;
  const [defaultValues, setDefaultValues] = useState<EditUserFormValues | undefined>();

  useEffect(() => {
    const fetchDefaultValues = async (): Promise<void> => {
      if (userId == null) {
        setDefaultValues(undefined);
        return;
      }
      const response = await fetchWithAuth(`${API_BASE_URL}/users/${userId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      const user = await response.json() as User;
      const newDefaultValues = {
        name: user.name,
        email: user.email,
        role: user.role,
        password: "",
        confirmPassword: "",
      };
      setDefaultValues(newDefaultValues);
      reset(newDefaultValues);
    };

    fetchDefaultValues();
  }, [userId]);

  const {
    register,
    control,
    handleSubmit,
    reset,
    clearErrors,
    setError,
    watch,
    formState: { errors },
  } = useForm<EditUserFormValues>({
    defaultValues,
  });
  const passwordValue = watch("password", "");
  const selectedRole = watch("role", defaultValues?.role);
  const permissionColumns = useMemo(() => {
    const permissions = ROLE_PERMISSIONS[selectedRole] ?? [];
    const midpoint = Math.ceil(permissions.length / 2);
    return [permissions.slice(0, midpoint), permissions.slice(midpoint)];
  }, [selectedRole]);

  const handleEdit = async (values: EditUserFormValues): Promise<void> => {
    clearErrors("email");

    if (userId == null || defaultValues == null) return;

    const response = await fetchWithAuth(`${API_BASE_URL}/users/${userId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...(values.name !== defaultValues.name && {name: values.name}),
        ...(values.email !== defaultValues.email && {email: values.email}),
        ...(values.role !== defaultValues.role && {role: values.role}),
        ...(values.password !== "" && {password: values.password}),
      }),
    });

    if (!response.ok) {
      setError(
        "email",
        { type: "server", message: "Unable to edit user. Please try again." },
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
      {defaultValues == null && <DialogContent
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          width: "100%",
          borderRadius: 3,
          border: "1px solid #ede9fe",
          boxShadow: "0 18px 40px rgba(17, 24, 39, 0.15)",
        }}
      >
        <CircularProgress />
      </DialogContent>}
      {defaultValues != null && <DialogContent
        sx={{
          width: "100%",
          borderRadius: 3,
          border: "1px solid #ede9fe",
          boxShadow: "0 18px 40px rgba(17, 24, 39, 0.15)",
        }}
      >
        <AuthLogo subtitle="Edit Existing User" />

        <Box component="form" onSubmit={handleSubmit(handleEdit)} noValidate>
          <Grid container spacing={2}>
            <FloatingTextField
              fullWidth
              label="Name"
              required
              placeholder="Enter name"
              size="small"
              error={Boolean(errors.name)}
              helperText={errors.name?.message}
              {...register("name", { required: "Required" })}
            />
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
                placeholder="Enter password (6-72 characters)"
                size="small"
                autoComplete="new-password"
                sx={{ mt: 2 }}
                error={Boolean(errors.password)}
                helperText={errors.password?.message}
                {...register("password", {
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
                placeholder="Confirm password"
                size="small"
                autoComplete="new-password"
                sx={{ mt: 2 }}
                error={Boolean(errors.confirmPassword)}
                helperText={errors.confirmPassword?.message}
                {...register("confirmPassword", {
                  validate: (value) => value === passwordValue || "Passwords do not match",
                })}
              />
            </Grid>
          </Grid>

          {/* Admins shouldn't be able to change their own roles while editing */}
          {!isEditingSelf && <>
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
                            color: isSelected ? "#7e22ce" : "#374151",
                            borderColor: isSelected ? "#9333ea" : "#d1d5db",
                            backgroundColor: isSelected ? "#faf5ff" : "#fff",
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
          </>}

          <Stack spacing={1.5} {...isEditingSelf && { sx: { mt: 3 } }}>
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
              Update User
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
                  color: "#374151",
                  borderColor: "#d1d5db",
                }}
              >
                Cancel
              </Button>
            </Stack>
          </Stack>
        </Box>
      </DialogContent>}
    </Dialog>
  );
};
