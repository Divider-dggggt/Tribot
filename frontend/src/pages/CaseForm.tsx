import React, { ReactElement } from "react";
import { useForm } from "react-hook-form";
import { 
  TextField, 
  Button, 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  Stack
} from '@mui/material';
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { addTriageCase } from "../store/triage/triageSlice";
import { ATSLevel } from "../types/triage";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";
import { formatCaseDateTime } from "../utils/date";

// Simple Send Icon
const SendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8 }}>
    <line x1="22" y1="2" x2="11" y2="13"></line>
    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
  </svg>
);

// Simple X Icon
const XIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8 }}>
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

export const CaseForm = (): ReactElement => {
  const dispatch = useDispatch();
  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const navigate = useNavigate();
  const details = watch('details', '');

  const onSubmit = (data: Record<string, string>) => {
    // TODO: fetch API request from backend for triage
    const priorities = Object.values(ATSLevel).filter((key) => typeof key === "number");
    const randomPriority = priorities[Math.floor(Math.random() * priorities.length)];
    dispatch(addTriageCase({
      id: data.patientID,
      name: data.patientName,
      date: formatCaseDateTime(),
      priority: randomPriority as ATSLevel,
      details: data.details,
    }));
    navigate("/", { state: { message: "Successfully created case", severity: "success" } });
  };

  return (
    <Box sx={{ maxWidth: PAGE_CONTENT_MAX_WIDTH, mx: 'auto' }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Create New Case
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Enter patient symptoms for AI triage assessment
        </Typography>
      </Box>

      <Card elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
        <CardContent sx={{ p: 4 }}>
          <form onSubmit={handleSubmit(onSubmit)}>
            
            {/* Patient Information */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                Patient Information
              </Typography>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" fontWeight="medium" sx={{ mb: 1 }}>
                    Patient ID
                  </Typography>
                  <TextField
                    fullWidth
                    placeholder="Enter patient ID"
                    {...register("patientID", { required: "Required" })}
                    error={!!errors.patientID}
                    helperText={errors.patientID?.message as string}
                    variant="outlined"
                    size="medium"
                    InputProps={{ sx: { borderRadius: 2 } }}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" fontWeight="medium" sx={{ mb: 1 }}>
                    Patient Name
                  </Typography>
                  <TextField
                    fullWidth
                    placeholder="Enter patient name"
                    {...register("patientName", { required: "Required" })}
                    error={!!errors.patientName}
                    helperText={errors.patientName?.message as string}
                    variant="outlined"
                    size="medium"
                    InputProps={{ sx: { borderRadius: 2 } }}
                  />
                </Grid>
              </Grid>
            </Box>

            {/* Case Details */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                Case Details
              </Typography>
              <TextField
                fullWidth
                placeholder="Enter case details here"
                {...register("details", { required: "Required" })}
                multiline
                rows={8}
                error={!!errors.details}
                helperText={errors.details?.message as string}
                variant="outlined"
                InputProps={{ sx: { borderRadius: 2 } }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {details.length} characters
              </Typography>
            </Box>

            {/* Buttons */}
            <Stack direction="row" spacing={2} sx={{ mt: 4, width: '100%' }}>
              <Button 
                type="submit" 
                variant="contained" 
                size="large"
                sx={{ 
                  flex: 1,
                  bgcolor: '#9333ea', 
                  '&:hover': { bgcolor: '#7e22ce' },
                  textTransform: 'none',
                  fontWeight: 'bold',
                  justifyContent: 'center',
                  px: 4,
                  py: 1.5,
                  borderRadius: 2
                }}
              >
                <SendIcon />
                Submit for Triage
              </Button>
              <Button 
                variant="outlined" 
                size="large"
                onClick={() => navigate('/')}
                sx={{ 
                  minWidth: 140,
                  color: '#374151',
                  borderColor: '#d1d5db',
                  '&:hover': { borderColor: '#9ca3af', bgcolor: '#f9fafb' },
                  textTransform: 'none',
                  fontWeight: 'medium',
                  px: 4,
                  py: 1.5,
                  borderRadius: 2
                }}
              >
                <Box component="span" sx={{ color: '#dc2626', display: 'inline-flex' }}>
                  <XIcon />
                </Box>
                Cancel
              </Button>
            </Stack>

          </form>
        </CardContent>
      </Card>
    </Box>
  );
};
