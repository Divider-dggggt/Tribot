import { ReactElement, useMemo } from "react";
import { Box, Button, Card, CardContent, Grid, Stack, TextField, Typography } from "@mui/material";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { AuthLogo } from "../components/AuthLogo";

const ROLE_OPTIONS = ["Doctor", "Nurse", "Admin", "Specialist"] as const;
const PERMISSIONS = [
  "Create new cases",
  "Override AI predictions",
  "Generate reports",
  "View all patient records",
  "Access evaluation tools",
  "Administrative access",
];

const requiredLabel = (text: string) => (
  <Typography variant="subtitle2" sx={{ mb: 0.75, color: "#374151", fontWeight: 600 }}>
    {text}
    <Box component="span" sx={{ color: "#dc2626", ml: 0.5 }}>
      *
    </Box>
  </Typography>
);

interface CreateAccountFormValues {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  userRole: (typeof ROLE_OPTIONS)[number];
  licenseNumber: string;
  department: string;
  username: string;
  password: string;
  confirmPassword: string;
}

export const CreateAccountPage = (): ReactElement => {
  const navigate = useNavigate();
  const permissionColumns = useMemo(
    () => [PERMISSIONS.slice(0, 3), PERMISSIONS.slice(3)],
    []
  );

  const defaultValues: CreateAccountFormValues = {
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    userRole: "Doctor",
    licenseNumber: "",
    department: "",
    username: "",
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
  } = useForm<CreateAccountFormValues>({
    defaultValues,
  });
  const passwordValue = watch("password", "");

  const handleCreate = (_values: CreateAccountFormValues): void => {
    navigate("/login");
  };

  const handleReset = () => {
    reset(defaultValues);
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
        py: 4,
      }}
    >
      <Card
        elevation={0}
        sx={{
          width: "100%",
          maxWidth: 760,
          borderRadius: 3,
          border: "1px solid #ede9fe",
          boxShadow: "0 18px 40px rgba(17, 24, 39, 0.15)",
        }}
      >
        <CardContent sx={{ p: { xs: 3, sm: 4.5 } }}>
          <AuthLogo subtitle="Create New User Account" />

          <Box component="form" onSubmit={handleSubmit(handleCreate)} noValidate>
            <Typography
              variant="h6"
              sx={{
                mb: 2.2,
                fontSize: "1.1rem",
                fontWeight: 700,
                color: "#111827",
                textDecoration: "underline",
                textDecorationColor: "#2563eb",
                textUnderlineOffset: 3,
              }}
            >
              Personal Information
            </Typography>

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
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
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
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
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
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
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle2" sx={{ mb: 0.75, color: "#374151", fontWeight: 600 }}>
                  Phone Number
                </Typography>
                <TextField
                  fullWidth
                  placeholder="(555) 123-4567"
                  size="small"
                  {...register("phone")}
                  InputProps={{ sx: { borderRadius: 2 } }}
                />
              </Grid>
            </Grid>

            <Typography variant="h6" sx={{ mt: 4, mb: 2, fontSize: "1.1rem", fontWeight: 700 }}>
              Professional Details
            </Typography>

            {requiredLabel("User Role")}
            <Controller
              name="userRole"
              control={control}
              rules={{ required: "Required" }}
              render={({ field }) => (
                <>
                  <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mb: 0.75 }}>
                    {ROLE_OPTIONS.map((role) => {
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
                  {errors.userRole?.message ? (
                    <Typography variant="caption" sx={{ color: "#dc2626", mb: 2.5, display: "block" }}>
                      {errors.userRole.message}
                    </Typography>
                  ) : (
                    <Box sx={{ mb: 2.5 }} />
                  )}
                </>
              )}
            />

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                {requiredLabel("License/Credential Number")}
                <TextField
                  fullWidth
                  placeholder="Enter license number"
                  size="small"
                  error={Boolean(errors.licenseNumber)}
                  helperText={errors.licenseNumber?.message}
                  {...register("licenseNumber", { required: "Required" })}
                  InputProps={{ sx: { borderRadius: 2 } }}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle2" sx={{ mb: 0.75, color: "#374151", fontWeight: 600 }}>
                  Department
                </Typography>
                <TextField
                  fullWidth
                  placeholder=""
                  size="small"
                  {...register("department")}
                  InputProps={{ sx: { borderRadius: 2 } }}
                />
              </Grid>
            </Grid>

            <Typography variant="h6" sx={{ mt: 4, mb: 2, fontSize: "1.1rem", fontWeight: 700 }}>
              Login Credentials
            </Typography>

            <Grid container spacing={2}>
              <Grid size={{ xs: 12 }}>
                {requiredLabel("Username")}
                <TextField
                  fullWidth
                  placeholder="Choose a username"
                  size="small"
                  error={Boolean(errors.username)}
                  helperText={errors.username?.message}
                  {...register("username", {
                    required: "Required",
                    minLength: {
                      value: 6,
                      message: "Minimum 6 characters",
                    },
                    pattern: {
                      value: /^[a-zA-Z0-9]+$/,
                      message: "Alphanumeric only",
                    },
                  })}
                  InputProps={{ sx: { borderRadius: 2 } }}
                />
                <Typography variant="caption" sx={{ color: "#6b7280", mt: 0.7, display: "block" }}>
                  Minimum 6 characters, alphanumeric only
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                {requiredLabel("Temporary Password")}
                <TextField
                  fullWidth
                  type="password"
                  placeholder="Enter password"
                  size="small"
                  error={Boolean(errors.password)}
                  helperText={errors.password?.message}
                  {...register("password", { required: "Required" })}
                  InputProps={{ sx: { borderRadius: 2 } }}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                {requiredLabel("Confirm Password")}
                <TextField
                  fullWidth
                  type="password"
                  placeholder="Confirm password"
                  size="small"
                  error={Boolean(errors.confirmPassword)}
                  helperText={errors.confirmPassword?.message}
                  {...register("confirmPassword", {
                    required: "Required",
                    validate: (value) => value === passwordValue || "Passwords do not match",
                  })}
                  InputProps={{ sx: { borderRadius: 2 } }}
                />
              </Grid>
            </Grid>

            <Box
              sx={{
                mt: 2,
                px: 1.5,
                py: 1.25,
                borderRadius: 1.5,
                bgcolor: "#eff6ff",
                color: "#1d4ed8",
                border: "1px solid #dbeafe",
                fontSize: "0.9rem",
              }}
            >
              User will be required to change password on first login
            </Box>

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
                Create Account
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
                  onClick={() => navigate("/login")}
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
        </CardContent>
      </Card>
    </Box>
  );
};
