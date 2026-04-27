import React, { type ReactElement } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
} from "@mui/material";
import { API_BASE_URL } from "../utils/constants";
import { dangerTextButtonSx } from "../utils/buttonStyles";
import { fetchWithAuth } from "../utils/auth";

interface UndoOverrideDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  caseId: number;
}

/**
 * Renders a dialog for undoing a case override.
 * @param {Object} props The component props.
 * @param {boolean} props.open Whether the dialog is open.
 * @param {function} props.onClose The callback function for closing the dialog.
 * @param {function} props.onSuccess The callback function for successful case undo override action.
 * @param {number} props.caseId The ID of the case to be overridden.
 * @returns {JSX.Element} A case undo override dialog.
 */
export const UndoOverrideDialog = ({
  open,
  onClose,
  onSuccess,
  caseId,
}: UndoOverrideDialogProps): ReactElement => {
  const undoOverride = async (): Promise<void> => {
    await fetchWithAuth(`${API_BASE_URL}/cases/${caseId}/ats/undo`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
    }).then(() => {
      onSuccess();
    });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose}>
      {/* <DialogTitle>Override ATS Classification</DialogTitle> */}
      <DialogContent>
        Are you sure you want to undo override?
      </DialogContent>
      <DialogActions>
        <Button
          onClick={onClose}
          sx={dangerTextButtonSx}
        >
          Cancel
        </Button>
        <Button variant="contained" onClick={undoOverride}>Undo</Button>
      </DialogActions>
    </Dialog>
  );
};
