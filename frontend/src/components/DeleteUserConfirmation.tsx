import { Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from "@mui/material";
import React, { ReactElement, useState } from "react";
import { fetchWithAuth } from "../utils/auth";
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
    >
      <DialogTitle>Confirm User Deactivation</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Are you sure you want to deactivate this user?
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>Cancel</Button>
        <Button
          onClick={handleDelete}
          disabled={loading}
          color="error"
          startIcon={loading && <CircularProgress size={20} />}
        >
          {loading ? "Deactivating..." : "Deactivate"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
