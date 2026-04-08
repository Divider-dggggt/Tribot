import { FormEvent, ReactElement } from "react";
import { Controller, useForm } from "react-hook-form";
import { 
  Alert,
  CircularProgress,
  Button, 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  Snackbar,
  Stack,
  MenuItem,
  InputAdornment,
} from '@mui/material';
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { ATSLevel, TriageApiResponse } from "../types/triage";
import { FloatingTextField } from "../components/FloatingTextField";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";
import { formatCaseDateTime } from "../utils/date";
import { API_BASE_URL } from "../utils/constants";

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
  age?: number;
  gender?: "Male" | "Female" | "Other";
  duration?: number;
  medications?: string;
  allergies?: string;
  risks?: string;
  temperature?: number;
  heartRate?: number;
  respirationRate?: number;
  bloodPressure?: string;
}

type RequiredFieldName = "patientID" | "patientName" | "details";

const parseAtsToLevel = (atsClassification: number): ATSLevel => {
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

const isValidBloodPressure = (value: string): boolean => /^\d{2,3}\/\d{2,3}$/.test(value);

const toOptionalInteger = (value: unknown): number | undefined => {
  if (typeof value !== "string") {
    return undefined;
  }
  const digits = value.replace(/\D/g, "");
  if (!digits) {
    return undefined;
  }
  const parsed = Number(digits);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const toOptionalTemperature = (value: unknown): number | undefined => {
  if (typeof value !== "string") {
    return undefined;
  }
  const trimmedValue = value.trim();
  if (!trimmedValue) {
    return undefined;
  }
  const parsed = Number(trimmedValue);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const handleIntegerInput = (event: FormEvent<HTMLInputElement | HTMLTextAreaElement>) => {
  const input = event.currentTarget as HTMLInputElement;
  input.value = input.value.replace(/\D/g, "");
};

const handleTemperatureInput = (event: FormEvent<HTMLInputElement | HTMLTextAreaElement>) => {
  const input = event.currentTarget as HTMLInputElement;
  const sanitized = input.value.replace(/[^\d.]/g, "");
  const [rawIntegerPart = "", ...rawDecimalParts] = sanitized.split(".");
  const integerPart = rawIntegerPart.slice(0, 3);

  if (rawDecimalParts.length === 0) {
    input.value = integerPart;
    return;
  }

  const decimalPart = rawDecimalParts.join("").slice(0, 1);
  input.value = decimalPart ? `${integerPart}.${decimalPart}` : `${integerPart}.`;
};

const formatMedicareCardField = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement, Element>): string => {
  const sanitized = event.target.value.replace(/[^\d/]/g, "");
  const hasSlash = sanitized.includes("/");

  if (hasSlash) {
    const [rawCardNumber = "", rawIRN = ""] = sanitized.split("/", 2);
    const cardNumber = rawCardNumber.replace(/\D/g, "").slice(0, 10);
    const IRN = rawIRN.replace(/\D/g, "").slice(0, 1);
    if (!cardNumber && !IRN) {
      return "";
    }
    if (!IRN) {
      return cardNumber;
    }
    return `${cardNumber}/${IRN}`;
  }

  const digits = sanitized.replace(/\D/g, "").slice(0, 11);
  if (digits.length === 0) {
    return "";
  }
  if (digits.length <= 10) {
    return digits;
  }
  return `${digits.slice(0, 10)}/${digits.slice(10, 11)}`;
};

const formatBloodPressureInput = (rawValue: string): string => {
  const sanitized = rawValue.replace(/[^\d/]/g, "");
  const hasSlash = sanitized.includes("/");

  if (hasSlash) {
    const [rawSystolic = "", rawDiastolic = ""] = sanitized.split("/", 2);
    const systolic = rawSystolic.replace(/\D/g, "").slice(0, 3);
    const diastolic = rawDiastolic.replace(/\D/g, "").slice(0, 3);
    if (!systolic && !diastolic) {
      return "";
    }
    return `${systolic}/${diastolic}`;
  }

  const digits = sanitized.replace(/\D/g, "").slice(0, 6);
  if (digits.length === 0) {
    return "";
  }
  if (digits.length < 3) {
    return digits;
  }
  if (digits.length === 3) {
    return `${digits}/`;
  }
  return `${digits.slice(0, 3)}/${digits.slice(3, 6)}`;
};

export const CaseForm = (): ReactElement => {
  const dispatch = useDispatch();
  const {
    register,
    handleSubmit,
    watch,
    setError,
    clearErrors,
    formState: { errors, isSubmitting },
    control,
  } = useForm<CaseFormValues>();
  const navigate = useNavigate();
  const details = watch('details', '');
  const requiredFieldNames: RequiredFieldName[] = ["patientID", "patientName", "details"];

  const isRequiredFieldName = (value: string): value is RequiredFieldName => (
    requiredFieldNames.includes(value as RequiredFieldName)
  );

  const handleInvalidCapture = (event: FormEvent<HTMLFormElement>) => {
    const target = event.target as HTMLInputElement | HTMLTextAreaElement | null;
    if (!target?.name || !isRequiredFieldName(target.name) || !target.validity.valueMissing) {
      return;
    }
    setError(target.name, {
      type: "required",
      message: "Required",
    });
  };

  const onSubmit = async (data: CaseFormValues) => {
    clearErrors("root.serverError");
    const allDetails: string[] = [data.details];
    if (data.age) allDetails.push(`age: ${data.age}`);
    if (data.gender) allDetails.push(`gender: ${data.gender}`);
    if (data.duration) allDetails.push(`duration: ${data.duration}`);
    if (data.medications) allDetails.push(`medications: ${data.medications}`);
    if (data.allergies) allDetails.push(`allergies: ${data.allergies}`);
    if (data.risks) allDetails.push(`risks: ${data.risks}`);
    if (data.temperature) allDetails.push(`temperature: ${data.temperature}`);
    if (data.heartRate) allDetails.push(`heartRate: ${data.heartRate}`);
    if (data.respirationRate) allDetails.push(`respirationRate: ${data.respirationRate}`);
    if (data.bloodPressure) allDetails.push(`bloodPressure: ${data.bloodPressure}`);

    try {
      const accessToken = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE_URL}/triage`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({
          name: data.patientName,
          medicare_number: data.patientID.replace("/", ""),
          case_details: allDetails.join("\n"),
        }),
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      const triageResult = await response.json() as TriageApiResponse;

      navigate(
        { pathname: "/dashboard", search: `?case=${triageResult.case_id}` },
        { state: { message: "Successfully created case", severity: "success" } }
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to submit case";
      setError("root.serverError", {
        type: "server",
        message,
      });
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
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <form onSubmit={handleSubmit(onSubmit)} onInvalidCapture={handleInvalidCapture}>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 2 }}>
              * Required fields
            </Typography>
            
            {/* Patient Information */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                Patient Information
              </Typography>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Controller
                    name="patientID"
                    control={control}
                    rules={{
                      required: "Required",
                      pattern: {
                        value: /^\d{10}\/\d{1}$/,
                        message: "Must include card number (10 digits) and IRN (1 digit)",
                      },
                    }}
                    render={({ field }) => (
                      <FloatingTextField
                        label="Medicare Card Number"
                        value={field.value ?? ""}
                        onBlur={field.onBlur}
                        onChange={(event) => {
                          field.onChange(formatMedicareCardField(event));
                          clearErrors("patientID");
                        }}
                        error={!!errors.patientID}
                        helperText={errors.patientID?.message as string}
                        fullWidth
                        required
                        size="small"
                        variant="outlined"
                        inputProps={{
                          inputMode: "numeric",
                          maxLength: 12,
                        }}
                      />
                    )}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FloatingTextField
                    fullWidth
                    required
                    label="Patient Name"
                    {...register("patientName", {
                      required: "Required",
                      onChange: () => clearErrors("patientName"),
                    })}
                    error={!!errors.patientName}
                    helperText={errors.patientName?.message as string}
                    variant="outlined"
                    size="small"
                  />
                </Grid>
              </Grid>
            </Box>

            {/* Case Details */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                Case Details
              </Typography>
              <FloatingTextField
                fullWidth
                required
                label="Case Details"
                {...register("details", {
                  required: "Required",
                  onChange: () => clearErrors("details"),
                })}
                multiline
                rows={8}
                error={!!errors.details}
                helperText={errors.details?.message as string}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {details.length} characters
              </Typography>
            </Box>

            {/* Clinical Characteristics */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                Clinical Characteristics
              </Typography>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FloatingTextField
                    label="Age"
                    fullWidth
                    size="small"
                    {...register("age", {
                      setValueAs: toOptionalInteger,
                    })}
                    inputProps={{
                      inputMode: "numeric",
                      maxLength: 3,
                      onInput: handleIntegerInput,
                    }}
                    InputProps={{
                      endAdornment: <InputAdornment position="end">years</InputAdornment>,
                    }}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FloatingTextField
                    {...register("gender")}
                    fullWidth
                    select
                    label="Gender"
                    size="small"
                  >
                    <MenuItem value={undefined}><em>Unspecified</em></MenuItem>
                    <MenuItem value="Male">Male</MenuItem>
                    <MenuItem value="Female">Female</MenuItem>
                    <MenuItem value="Other">Other</MenuItem>
                  </FloatingTextField>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FloatingTextField
                    label="Symptom Duration"
                    fullWidth
                    size="small"
                    {...register("duration", {
                      setValueAs: toOptionalInteger,
                    })}
                    inputProps={{
                      inputMode: "numeric",
                      maxLength: 4,
                      onInput: handleIntegerInput,
                    }}
                    InputProps={{
                      endAdornment: <InputAdornment position="end">days</InputAdornment>,
                    }}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FloatingTextField
                    {...register("temperature", {
                      setValueAs: toOptionalTemperature,
                    })}
                    label="Body Temperature"
                    fullWidth
                    size="small"
                    variant="outlined"
                    inputProps={{
                      inputMode: "decimal",
                      maxLength: 5,
                      onInput: handleTemperatureInput,
                    }}
                    InputProps={{
                      endAdornment: <InputAdornment position="end">℃</InputAdornment>,
                    }}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FloatingTextField
                    label="Heart Rate"
                    fullWidth
                    size="small"
                    {...register("heartRate", {
                      setValueAs: toOptionalInteger,
                    })}
                    inputProps={{
                      inputMode: "numeric",
                      maxLength: 3,
                      onInput: handleIntegerInput,
                    }}
                    InputProps={{
                      endAdornment: <InputAdornment position="end">bpm</InputAdornment>,
                    }}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FloatingTextField
                    label="Respiration Rate"
                    fullWidth
                    size="small"
                    {...register("respirationRate", {
                      setValueAs: toOptionalInteger,
                    })}
                    inputProps={{
                      inputMode: "numeric",
                      maxLength: 3,
                      onInput: handleIntegerInput,
                    }}
                    InputProps={{
                      endAdornment: <InputAdornment position="end">breaths/min</InputAdornment>,
                    }}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 12 }}>
                  <Controller
                    name="bloodPressure"
                    control={control}
                    rules={{
                      validate: (value) => {
                        if (!value || !value.trim()) {
                          return true;
                        }
                        return isValidBloodPressure(value) || "Format must be Systolic/Diastolic (e.g., 120/80)";
                      },
                    }}
                    render={({ field }) => (
                      <FloatingTextField
                        label="Blood Pressure"
                        value={field.value ?? ""}
                        onBlur={field.onBlur}
                        onChange={(event) => {
                          field.onChange(formatBloodPressureInput(event.target.value));
                          clearErrors("bloodPressure");
                        }}
                        error={!!errors.bloodPressure}
                        helperText={errors.bloodPressure?.message as string}
                        fullWidth
                        size="small"
                        variant="outlined"
                        inputProps={{
                          inputMode: "numeric",
                          maxLength: 7,
                          placeholder: "120/80",
                        }}
                        InputProps={{
                          endAdornment: <InputAdornment position="end">mmHg</InputAdornment>,
                        }}
                      />
                    )}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FloatingTextField
                    label="Medications"
                    fullWidth
                    {...register("medications")}
                    multiline
                    rows={4}
                    size="small"
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FloatingTextField
                    label="Allergies"
                    fullWidth
                    {...register("allergies")}
                    multiline
                    rows={4}
                    size="small"
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 12 }}>
                  <FloatingTextField
                    label="Risk Factors & Comorbidities"
                    fullWidth
                    {...register("risks")}
                    multiline
                    rows={4}
                    size="small"
                  />
                </Grid>
              </Grid>
            </Box>

            {/* Buttons */}
            <Stack direction="row" spacing={2} sx={{ mt: 4, pt: 3, borderTop: "1px solid #e5e7eb", width: '100%' }}>
              <Button 
                type="submit" 
                variant="contained" 
                size="large"
                disabled={isSubmitting}
                sx={{ 
                  flex: 1,
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
        open={Boolean(errors.root?.serverError?.message)}
        autoHideDuration={5000}
        onClose={() => clearErrors("root.serverError")}
      >
        <Alert onClose={() => clearErrors("root.serverError")} severity="error" sx={{ width: "100%" }}>
          {errors.root?.serverError?.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};
