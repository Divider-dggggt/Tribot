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
import { fetchWithAuth, getDecodedToken } from "../utils/auth";
import { IconButton } from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import DoDisturbOnIcon from "@mui/icons-material/DoDisturbOn";
import Tooltip from "@mui/material/Tooltip";
import { EditUserForm } from "./EditUserForm";
import { DeleteUserConfirmation } from "./DeleteUserConfirmation";
import { DANGER_COLORS } from "../utils/buttonStyles";

const getRoleChipStyles = (role: UserRole) => {
  if (role === UserRole.Admin) {
    return { bgcolor: "#ede9fe", color: "#6d28d9" };
  }
  if (role === UserRole.Clinician) {
    return { bgcolor: "#dcfce7", color: "#166534" };
  }
  return { bgcolor: "#e0f2fe", color: "#0c4a6e" };
};

/**
 * Renders a table of users (admins, clinicians, researchers) with actionable buttons for user management.
 */
export const UsersTable = (): ReactElement => {
  const selfUserId = getDecodedToken()?.user_id;
  const [users, setUsers] = useState<User[]>([]);
  const [isCreatingUser, setIsCreatingUser] = useState<boolean>(false);
  const handleOpenCreateForm = () => setIsCreatingUser(true);
  const handleCloseCreateForm = () => setIsCreatingUser(false);
  const [deletingUserId, setDeletingUserId] = useState<number | undefined>();
  const isDeletingUser = deletingUserId != null;
  const handleOpenDeleteDialog = (userId: number) => setDeletingUserId(userId);
  const handleCloseDeleteDialog = () => setDeletingUserId(undefined);
  const [editingUserId, setEditingUserId] = useState<number | undefined>();
  const isEditingUser = editingUserId != null;
  const handleOpenEditForm = (userId: number) => setEditingUserId(userId);
  const handleCloseEditForm = () => setEditingUserId(undefined);

  useEffect(() => {
    const fetchUsers = async (): Promise<void> => {
      const response = await fetchWithAuth(`${API_BASE_URL}/users`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      const users = await response.json() as User[];
      setUsers(users);
    };

    if (!isCreatingUser && !isEditingUser && !isDeletingUser) {
      fetchUsers();
    }
  }, [isCreatingUser, isEditingUser, isDeletingUser]);

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
          variant="contained"
          onClick={handleOpenCreateForm}
          sx={{
            width: { xs: "100%", sm: "auto" },
            minWidth: { sm: 130 },
            px: 2.5,
            py: 1.1,
            borderRadius: 2,
            fontSize: "0.95rem",
            fontWeight: 700,
            whiteSpace: "nowrap",
          }}
        >
          Add User
        </Button>
      </Stack>
      <Card elevation={0} sx={{ border: "1px solid #e5e7eb", borderRadius: 2 }}>
        <CardContent
          sx={{
            p: 0,
            "&:last-child": {
              pb: 0,
            },
          }}
        >
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
                  <TableCell sx={{ color: "#6b7280", fontWeight: 700, borderBottomColor: "#e5e7eb" }} align="center">Actions</TableCell>
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
                    hover
                    sx={{
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
                    <TableCell align="center">
                      <Tooltip title="Edit User">
                        <IconButton onClick={() => handleOpenEditForm(user.id)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      {selfUserId !== user.id && <Tooltip title="Deactivate User">
                        <IconButton
                          onClick={() => handleOpenDeleteDialog(user.id)}
                          sx={{
                            color: "#6b7280",
                            transition: "all 160ms ease",
                            "&:hover": {
                              color: DANGER_COLORS.hoverText,
                              backgroundColor: DANGER_COLORS.hoverBackground,
                            },
                          }}
                        >
                          <DoDisturbOnIcon />
                        </IconButton>
                      </Tooltip>}
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
      <EditUserForm
        userId={editingUserId}
        onClose={handleCloseEditForm}
      />
      <DeleteUserConfirmation
        userId={deletingUserId}
        onClose={handleCloseDeleteDialog}
      />
    </Box>
  );
};
