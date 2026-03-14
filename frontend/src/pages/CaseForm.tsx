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
  MenuItem,
  FormControlLabel,
  Checkbox,
  Stack
} from '@mui/material';
import { useNavigate } from "react-router-dom";

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
  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    defaultValues: {
      triageLevel: "ATS-3",
    },
  });
  const navigate = useNavigate();
  const symptoms = watch('symptoms', '');

  const onSubmit = (data: Record<string, string>) => {
    console.log(data);
    navigate("/", { state: { message: "Successfully created case", severity: "success" } });
  };

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
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
                <Grid item xs={12} md={6}>
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
                <Grid item xs={12} md={6}>
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

            {/* Symptom Description */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                Symptom Description
              </Typography>
              <TextField
                fullWidth
                placeholder="Describe the patient's symptoms in detail..."
                {...register("symptoms", { required: "Required" })}
                multiline
                rows={8}
                error={!!errors.symptoms}
                helperText={errors.symptoms?.message as string}
                variant="outlined"
                InputProps={{ sx: { borderRadius: 2 } }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {symptoms.length} characters
              </Typography>
            </Box>

            {/* ATS Triage Level */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                ATS Triage Level
              </Typography>
              <Typography variant="subtitle2" fontWeight="medium" sx={{ mb: 1 }}>
                Triage Category
              </Typography>
              <TextField
                fullWidth
                select
                {...register("triageLevel", { required: "Required" })}
                error={!!errors.triageLevel}
                helperText={errors.triageLevel?.message as string}
                variant="outlined"
                InputProps={{ sx: { borderRadius: 2 } }}
              >
                <MenuItem value="ATS-1">ATS-1 (High)</MenuItem>
                <MenuItem value="ATS-2">ATS-2</MenuItem>
                <MenuItem value="ATS-3">ATS-3 (Medium)</MenuItem>
                <MenuItem value="ATS-4">ATS-4</MenuItem>
                <MenuItem value="ATS-5">ATS-5 (Low)</MenuItem>
              </TextField>
            </Box>

            {/* Additional Information */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                Additional Information (Optional)
              </Typography>
              
              <FormControlLabel
                control={<Checkbox {...register("medicalHistory")} sx={{ color: '#9ca3af', '&.Mui-checked': { color: '#9333ea' } }} />}
                label={<Typography variant="body2" fontWeight="medium">Patient has relevant medical history</Typography>}
                sx={{ mb: 2 }}
              />

              <Typography variant="subtitle2" fontWeight="medium" sx={{ mb: 1, mt: 2 }}>
                Current Medications
              </Typography>
              <TextField
                fullWidth
                placeholder="List current medications (if any)"
                {...register("medications")}
                variant="outlined"
                InputProps={{ sx: { borderRadius: 2 } }}
              />
            </Box>

            {/* Buttons */}
            <Stack direction="row" spacing={2} sx={{ mt: 4 }}>
              <Button 
                type="submit" 
                variant="contained" 
                size="large"
                sx={{ 
                  bgcolor: '#9333ea', 
                  '&:hover': { bgcolor: '#7e22ce' },
                  textTransform: 'none',
                  fontWeight: 'bold',
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
                <XIcon />
                Cancel
              </Button>
            </Stack>

          </form>
        </CardContent>
      </Card>
    </Box>
  );
};
