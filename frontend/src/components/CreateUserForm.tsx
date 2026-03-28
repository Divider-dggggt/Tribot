import { ReactElement, useMemo } from "react";
import { Box, Button, Dialog, DialogContent, Grid, Stack, TextField, Typography } from "@mui/material";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { AuthLogo } from "./AuthLogo";
import { UserRole } from "../types/user";
import { API_BASE_URL } from "../utils/constants";

const PERMISSIONS = [
  "Create new cases",
  "Override AI predictions",
  "Generate reports",
  "View all patient records",
  "Access evaluation tools",
  "Administrative access",
];

const requiredLabel = (text: string) => (
  <Typography variant="subtitle2" sx={{ mb: 0.75, mt: 1, color: "#374151", fontWeight: 600 }}>
    {text}
    <Box component="span" sx={{ color: "#dc2626", ml: 0.5 }}>
      *
    </Box>
  </Typography>
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
  const navigate = useNavigate();
  const permissionColumns = useMemo(
    () => [PERMISSIONS.slice(0, 3), PERMISSIONS.slice(3)],
    []
  );

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
    watch,
    formState: { errors },
  } = useForm<CreateUserFormValues>({
    defaultValues,
  });
  const passwordValue = watch("password", "");

  const handleCreate = async (values: CreateUserFormValues): Promise<void> => {
    const accessToken = localStorage.getItem("access_token");
    await fetch(`${API_BASE_URL}/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify({
        name: `${values.firstName} ${values.lastName}`,
        email: values.email,
        role: values.role,
        password: values.password,
      }),
    });
    handleReset();
    onClose();
  };

  const handleReset = () => {
    reset(defaultValues);
  };

  return (
    <Dialog open={open} onClose={onClose} disablePortal scroll="body">
      <DialogContent
        sx={{
          width: "100%",
          maxWidth: 760,
          borderRadius: 3,
          border: "1px solid #ede9fe",
          boxShadow: "0 18px 40px rgba(17, 24, 39, 0.15)",
        }}
      >
        <AuthLogo subtitle="Create New User" />

        <Box component="form" onSubmit={handleSubmit(handleCreate)} noValidate>
          {requiredLabel("First Name")}
          <TextField
            fullWidth
            placeholder="Enter first name"
            size="small"
            error={Boolean(errors.firstName)}
            helperText={errors.firstName?.message}
            {...register("firstName", { required: "Required" })}
            InputProps={{ sx: { borderRadius: 2 } }}
          />
          {requiredLabel("Last Name")}
          <TextField
            fullWidth
            placeholder="Enter last name"
            size="small"
            error={Boolean(errors.lastName)}
            helperText={errors.lastName?.message}
            {...register("lastName", { required: "Required" })}
            InputProps={{ sx: { borderRadius: 2 } }}
          />
          {requiredLabel("Email Address")}
          <TextField
            fullWidth
            placeholder="email@example.com"
            size="small"
            error={Boolean(errors.email)}
            helperText={errors.email?.message}
            {...register("email", {
              required: "Required",
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: "Enter a valid email address",
              },
            })}
            InputProps={{ sx: { borderRadius: 2 } }}
          />
          {requiredLabel("Temporary Password")}
          <TextField
            fullWidth
            type="password"
            placeholder="Enter password"
            size="small"
            autoComplete="new-password"
            error={Boolean(errors.password)}
            helperText={errors.password?.message}
            {...register("password", { required: "Required" })}
            InputProps={{ sx: { borderRadius: 2 } }}
          />
          {requiredLabel("Confirm Password")}
          <TextField
            fullWidth
            type="password"
            placeholder="Confirm password"
            size="small"
            autoComplete="new-password"
            error={Boolean(errors.confirmPassword)}
            helperText={errors.confirmPassword?.message}
            {...register("confirmPassword", {
              required: "Required",
              validate: (value) => value === passwordValue || "Passwords do not match",
            })}
            InputProps={{ sx: { borderRadius: 2 } }}
          />

          {requiredLabel("User Role")}
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
                          "&:hover": {
                            borderColor: "#9333ea",
                            backgroundColor: "#faf5ff",
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
                textTransform: "none",
                borderRadius: 2,
                py: 1.25,
                fontWeight: 600,
                fontSize: "1.05rem",
                bgcolor: "#9333ea",
                "&:hover": {
                  bgcolor: "#7e22ce",
                },
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
                  textTransform: "none",
                  borderRadius: 2,
                  py: 1.15,
                  color: "#374151",
                  borderColor: "#d1d5db",
                  "&:hover": { borderColor: "#9ca3af", backgroundColor: "#f9fafb" },
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
                  textTransform: "none",
                  borderRadius: 2,
                  py: 1.15,
                  color: "#374151",
                  borderColor: "#d1d5db",
                  "&:hover": { borderColor: "#9ca3af", backgroundColor: "#f9fafb" },
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
