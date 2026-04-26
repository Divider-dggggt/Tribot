import {
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";
import React, { ReactElement, useState } from "react";
import { fetchWithAuth } from "../utils/auth";
import { dangerOutlinedButtonSx } from "../utils/buttonStyles";
import { API_BASE_URL } from "../utils/constants";

interface DeleteUserConfirmationProps {
  userId?: number;
  onClose: () => void;
}

export const DeleteUserConfirmation = ({
  userId,
  onClose,
}: DeleteUserConfirmationProps): ReactElement => {
  const open = userId != null;
  const [loading, setLoading] = useState<boolean>(false);

  const handleClose = (): void => {
    if (loading) return;
    onClose();
  };

  const handleDelete = async (): Promise<void> => {
    setLoading(true);
    try {
      await fetchWithAuth(`${API_BASE_URL}/users/${userId}/deactivate`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
      });
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
      handleClose();
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
        Confirm User Deactivation
      </DialogTitle>
      <DialogContent sx={{ px: 3, pb: 1.5 }}>
        <DialogContentText sx={{ fontSize: "1rem", color: "#6b7280" }}>
          Are you sure you want to deactivate this user?
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 3, pt: 0.5, gap: 1.5 }}>
        <Button
          onClick={handleClose}
          disabled={loading}
          variant="outlined"
          sx={{
            borderRadius: 2,
            py: 1.1,
            px: 2.25,
            color: "#374151",
            borderColor: "#d1d5db",
          }}
        >
          Cancel
        </Button>
        <Button
          onClick={handleDelete}
          disabled={loading}
          variant="outlined"
          startIcon={loading ? <CircularProgress size={16} color="inherit" /> : undefined}
          sx={{
            borderRadius: 2,
            py: 1.1,
            px: 2.25,
            ...dangerOutlinedButtonSx,
          }}
        >
          {loading ? "Deactivating..." : "Deactivate"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
