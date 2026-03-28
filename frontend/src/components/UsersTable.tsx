import { useEffect, useState, type ReactElement } from "react";
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import { API_BASE_URL } from "../utils/constants";
import { User } from "../types/user";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import { formatCaseDateTime } from "../utils/date";

export const UsersTable = (): ReactElement => {
  const [users, setUsers] = useState<User[]>([]);

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

    fetchUsers();
  }, []);

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
          onClick={() => {}}
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
      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell align="right">Email</TableCell>
              <TableCell align="right">Role</TableCell>
              <TableCell align="right">Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow
                key={user.name}
                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
              >
                <TableCell component="th" scope="row">
                  {user.name}
                </TableCell>
                <TableCell align="right">{user.email}</TableCell>
                <TableCell align="right">{user.role}</TableCell>
                <TableCell align="right">{formatCaseDateTime(new Date(user.created_at))}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};
