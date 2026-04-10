import React, { type ReactElement } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
} from "@mui/material";
import { ATSLevel } from "../types/triage";
import { Controller, useForm } from "react-hook-form";
import { API_BASE_URL } from "../utils/constants";
import { FloatingTextField } from "./FloatingTextField";

interface OverrideDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialValue: ATSLevel;
  caseId: number;
}

export const OverrideDialog = ({
  open,
  onClose,
  onSuccess,
  initialValue,
  caseId,
}: OverrideDialogProps): ReactElement => {
  const { control, handleSubmit, reset } = useForm({
    defaultValues: { atsOverride: initialValue }
  });

  const onSubmit = async (data: { atsOverride: ATSLevel }): Promise<void> => {
    if (data.atsOverride !== initialValue) {
      const accessToken = localStorage.getItem("access_token");
      await fetch(`${API_BASE_URL}/cases/${caseId}/ats`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({
          ats_classification: data.atsOverride + 1,
        }),
      }).then(() => {
        onSuccess();
      });
    }
    onClose();
    reset(); // Clear form after success
  };

  const onCancel = () => {
    reset(); // Clear current input on cancel
    onClose();
  };

  return (
    <Dialog open={open} onClose={onCancel}>
      <DialogTitle>Override ATS Classification</DialogTitle>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent>
          <Controller
            name="atsOverride"
            control={control}
            rules={{ required: "Selection is required" }}
            render={({ field, fieldState: { error } }) => (
              <FloatingTextField
                select
                fullWidth
                label="Select ATS Classification"
                {...field}
                required
                error={!!error}
                helperText={error?.message}
              >
                <MenuItem value={ATSLevel["ATS-1"]}>ATS 1</MenuItem>
                <MenuItem value={ATSLevel["ATS-2"]}>ATS 2</MenuItem>
                <MenuItem value={ATSLevel["ATS-3"]}>ATS 3</MenuItem>
                <MenuItem value={ATSLevel["ATS-4"]}>ATS 4</MenuItem>
                <MenuItem value={ATSLevel["ATS-5"]}>ATS 5</MenuItem>
              </FloatingTextField>
            )}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onCancel}>Cancel</Button>
          <Button type="submit" variant="contained">Override</Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
