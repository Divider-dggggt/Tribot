import React, { ReactElement, useState } from "react";
import { useForm } from "react-hook-form";
import { 
  Alert,
  CircularProgress,
  TextField, 
  Button, 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  Snackbar,
  Stack
} from '@mui/material';
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { addTriageCase, getTriageCases } from "../store/triage/triageSlice";
import { ATSLevel, TriageCase } from "../types/triage";
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

interface CaseFormValues {
  patientID: string;
  patientName: string;
  details: string;
}

interface TriageApiResponse {
  case_id: number;
  severity_flagged: boolean;
  soap_summary: string;
  ats_classification: number;
  confidence_score: number;
  flagged_keywords: string | null;
}

const API_BASE_URL = "http://localhost:8000";

const mapBackendAtsToLevel = (atsClassification: number): ATSLevel => {
  const boundedAts = Math.min(5, Math.max(1, Math.round(atsClassification)));
  return (boundedAts - 1) as ATSLevel;
};

const normalizeConfidence = (rawScore: number): number => {
  if (!Number.isFinite(rawScore)) {
    return 0;
  }

  const ratio = rawScore > 1 ? rawScore / 100 : rawScore;
  return Math.max(0, Math.min(1, ratio));
};

const readErrorMessage = async (response: Response): Promise<string> => {
  try {
    const data = await response.json() as { detail?: string };
    if (typeof data.detail === "string" && data.detail.trim()) {
      return data.detail;
    }
  } catch {
    // Ignore parse errors and use fallback.
  }

  return `Request failed with status ${response.status}`;
};

export const CaseForm = (): ReactElement => {
  const dispatch = useDispatch();
  const triageCases = useSelector(getTriageCases);
  const { register, handleSubmit, watch, formState: { errors } } = useForm<CaseFormValues>();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const details = watch('details', '');

  const onSubmit = async (data: CaseFormValues) => {
    setSubmitError(null);
    setIsSubmitting(true);

    try {
      const accessToken = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE_URL}/triage`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({
          case_details: data.details,
        }),
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      const triageResult = await response.json() as TriageApiResponse;
      const newCase: TriageCase = {
        caseId: triageResult.case_id,
        atsClassification: triageResult.ats_classification,
        safetyOverride: triageResult.severity_flagged,
        flaggedKeywords: triageResult.flagged_keywords,
        soapSummary: triageResult.soap_summary,
      id: data.patientID,
      name: data.patientName,
      date: formatCaseDateTime(),
        priority: mapBackendAtsToLevel(triageResult.ats_classification),
        confidence: normalizeConfidence(triageResult.confidence_score),
      details: data.details,
    };

      const severitySortedCases = [...triageCases, newCase].sort(
        (a, b) => a.priority - b.priority
      );
      const newCaseIndex = severitySortedCases.findIndex((currentCase) => currentCase === newCase);

      dispatch(addTriageCase(newCase));
      navigate(
        { pathname: "/dashboard", search: `?case=${newCaseIndex}` },
        { state: { message: "Successfully created case", severity: "success" } }
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to submit case";
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
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
                disabled={isSubmitting}
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
                {isSubmitting ? (
                  <CircularProgress size={20} color="inherit" sx={{ mr: 1 }} />
                ) : (
                  <SendIcon />
                )}
                {isSubmitting ? "Submitting..." : "Submit for Triage"}
              </Button>
              <Button 
                variant="outlined" 
                size="large"
                onClick={() => navigate('/dashboard')}
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

      <Snackbar
        open={Boolean(submitError)}
        autoHideDuration={5000}
        onClose={() => setSubmitError(null)}
      >
        <Alert onClose={() => setSubmitError(null)} severity="error" sx={{ width: "100%" }}>
          {submitError}
        </Alert>
      </Snackbar>
    </Box>
  );
};
