import { useEffect, useState, type ReactElement } from "react";
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import { API_BASE_URL } from "../utils/constants";
import { User, UserRole } from "../types/user";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import { formatCaseDateTime } from "../utils/date";
import { CreateUserForm } from "./CreateUserForm";

const getRoleChipStyles = (role: UserRole) => {
  if (role === UserRole.Admin) {
    return { bgcolor: "#ede9fe", color: "#6d28d9" };
  }
  if (role === UserRole.Clinician) {
    return { bgcolor: "#dcfce7", color: "#166534" };
  }
  return { bgcolor: "#e0f2fe", color: "#0c4a6e" };
};

export const UsersTable = (): ReactElement => {
  const [users, setUsers] = useState<User[]>([]);
  const [isCreatingUser, setIsCreatingUser] = useState<boolean>(false);
  const handleOpenCreateForm = () => setIsCreatingUser(true);
  const handleCloseCreateForm = () => setIsCreatingUser(false);

  useEffect(() => {
    const accessToken = localStorage.getItem("access_token");
    const fetchUsers = async (): Promise<void> => {
      const response = await fetch(`${API_BASE_URL}/users`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
      });
      const users = await response.json() as User[];
      setUsers(users);
    };

    if (!isCreatingUser) {
      fetchUsers();
    }
  }, [isCreatingUser]);

  return (
    <Box sx={{ maxWidth: PAGE_CONTENT_MAX_WIDTH, mx: "auto" }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 4 }}
      >
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
            All Users
          </Typography>
        </Box>
        <Button
          variant="outlined"
          onClick={handleOpenCreateForm}
          sx={{
            color: "#7c3aed",
            borderColor: "#c4b5fd",
            px: 2,
            py: 1,
            borderRadius: 2,
            textTransform: "none",
            fontWeight: "bold",
            "&:hover": {
              borderColor: "#a78bfa",
              bgcolor: "#f5f3ff",
            },
          }}
        >
          Add User
        </Button>
      </Stack>
      <Card elevation={0} sx={{ border: "1px solid #e5e7eb", borderRadius: 2 }}>
        <CardContent sx={{ p: 0 }}>
          <Box sx={{ px: 3, py: 2.5, borderBottom: "1px solid #e5e7eb" }}>
            <Typography variant="h6" fontWeight="bold">
              User Directory
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Manage team accounts and access roles.
            </Typography>
          </Box>
          <TableContainer component={Paper} elevation={0}>
            <Table sx={{ minWidth: 700 }} aria-label="users table">
              <TableHead>
                <TableRow sx={{ bgcolor: "#faf5ff" }}>
                  <TableCell sx={{ color: "#6b7280", fontWeight: 700, borderBottomColor: "#e5e7eb" }}>Name</TableCell>
                  <TableCell sx={{ color: "#6b7280", fontWeight: 700, borderBottomColor: "#e5e7eb" }}>Email</TableCell>
                  <TableCell sx={{ color: "#6b7280", fontWeight: 700, borderBottomColor: "#e5e7eb" }}>Role</TableCell>
                  <TableCell sx={{ color: "#6b7280", fontWeight: 700, borderBottomColor: "#e5e7eb" }}>Created</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} sx={{ py: 6, textAlign: "center", color: "#6b7280" }}>
                      No users found
                    </TableCell>
                  </TableRow>
                )}
                {users.map((user) => (
                  <TableRow
                    key={user.id}
                    sx={{
                      "&:hover, &.MuiTableRow-hover:hover": { bgcolor: "#f5f3ff" },
                      "&:hover > *, &.MuiTableRow-hover:hover > *": { bgcolor: "#f5f3ff" },
                      "&:last-child td, &:last-child th": { border: 0 },
                    }}
                  >
                    <TableCell component="th" scope="row" sx={{ py: 1.8 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "#111827" }}>
                        {user.name}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ color: "#374151" }}>{user.email}</TableCell>
                    <TableCell>
                      <Chip
                        label={user.role}
                        size="small"
                        sx={{
                          ...getRoleChipStyles(user.role),
                          fontWeight: 700,
                          borderRadius: 1.5,
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ color: "#6b7280", whiteSpace: "nowrap" }}>
                      {formatCaseDateTime(new Date(user.created_at))}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
      <CreateUserForm
        open={isCreatingUser}
        onClose={handleCloseCreateForm}
      />
    </Box>
  );
};
