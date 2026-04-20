import { useEffect, useState, type ReactElement } from "react";
import { API_BASE_URL } from "../utils/constants";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import { fetchWithAuth } from "../utils/auth";
import { Alert, CircularProgress } from "@mui/material";

interface ModelMetricsAPIResponse {
  model_name: string;
  metrics: {
    f1_score: number;
    precision: number;
    recall: number;
    confusion_matrix: number[][];
  };
}

const DEFAULT_LABELS = ["ATS-1", "ATS-2", "ATS-3", "ATS-4", "ATS-5"];

const buildMatrixLabels = (matrix: number[][]): string[] => {
  const largestRowLength = matrix.reduce((max, row) => Math.max(max, row.length), 0);
  const size = Math.max(DEFAULT_LABELS.length, matrix.length, largestRowLength);
  return Array.from({ length: size }, (_, index) => DEFAULT_LABELS[index] ?? `ATS-${index + 1}`);
};

const getMaxMatrixValue = (matrix: number[][]): number => {
  let maxValue = 0;
  matrix.forEach((row) => {
    row.forEach((value) => {
      if (Number.isFinite(value) && value > maxValue) {
        maxValue = value;
      }
    });
  });
  return Math.max(1, maxValue);
};

const getMatrixCellBackground = (value: number, maxValue: number, isDiagonal: boolean): string => {
  const normalized = Math.max(0, Math.min(1, value / maxValue));
  const alpha = (isDiagonal ? 0.2 : 0.08) + normalized * (isDiagonal ? 0.58 : 0.4);
  return `rgba(147, 51, 234, ${alpha.toFixed(3)})`;
};

export const Metrics = (): ReactElement => {
  const [metrics, setMetrics] = useState<ModelMetricsAPIResponse | undefined>();
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchMetrics = async (): Promise<void> => {
      setIsLoading(true);
      try {
        const response = await fetchWithAuth(`${API_BASE_URL}/model-metrics`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });
        const metrics_response = await response.json();
        setMetrics(metrics_response);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  const formatMetricValue = (value: number): string => {
    if (!Number.isFinite(value)) return "0.00";
    return value.toFixed(2);
  };

  const matrixData = metrics?.metrics.confusion_matrix ?? [];
  const matrixLabels = buildMatrixLabels(matrixData);
  const maxMatrixValue = getMaxMatrixValue(matrixData);

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
            Metrics
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Model evaluation snapshot and ATS classification performance
          </Typography>
        </Box>
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
              Confusion Matrix
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Rows represent actual ATS labels, columns represent predicted ATS labels.
            </Typography>
          </Box>

          {isLoading && (
            <Box
              display="flex"
              justifyContent="center"
              alignItems="center"
              sx={{ p: 4, minHeight: 260 }}
            >
              <CircularProgress />
            </Box>
          )}

          {!isLoading && metrics == null && (
            <Box sx={{ p: 3 }}>
              <Alert severity="info" sx={{ borderRadius: 2 }}>
                Model metrics are not available right now. Please try again later.
              </Alert>
            </Box>
          )}

          {!isLoading && metrics != null && (
            <Box sx={{ p: 3 }}>
              <Box
                sx={{
                  p: 2.5,
                  borderRadius: 2,
                  border: "1px solid #ede9fe",
                  bgcolor: "#faf5ff",
                  overflowX: "auto",
                }}
              >
                <Box sx={{ width: "max-content", mx: "auto" }}>
                  <Typography
                    variant="caption"
                    sx={{ display: "block", mb: 1, color: "#6b7280", textAlign: "center", fontWeight: 600 }}
                  >
                    Predicted Label
                  </Typography>
                  <Box
                    component="table"
                    sx={{
                      borderCollapse: "separate",
                      borderSpacing: "6px",
                    }}
                  >
                    <Box component="thead">
                      <Box component="tr">
                        <Box component="th" />
                        {matrixLabels.map((label) => (
                          <Box
                            key={`predicted-${label}`}
                            component="th"
                            sx={{
                              minWidth: 64,
                              px: 1,
                              py: 0.5,
                              borderRadius: 1.2,
                              bgcolor: "#f3f4f6",
                              color: "#4b5563",
                              textAlign: "center",
                              fontSize: "0.75rem",
                              fontWeight: 700,
                            }}
                          >
                            {label}
                          </Box>
                        ))}
                      </Box>
                    </Box>
                    <Box component="tbody">
                      {matrixLabels.map((actualLabel, rowIndex) => (
                        <Box key={`actual-row-${actualLabel}`} component="tr">
                          <Box
                            component="th"
                            sx={{
                              minWidth: 78,
                              px: 1.25,
                              py: 1,
                              borderRadius: 1.2,
                              bgcolor: "#f3f4f6",
                              color: "#4b5563",
                              textAlign: "center",
                              fontSize: "0.78rem",
                              fontWeight: 700,
                            }}
                          >
                            {actualLabel}
                          </Box>
                          {matrixLabels.map((predictedLabel, colIndex) => {
                            const value = matrixData[rowIndex]?.[colIndex] ?? 0;
                            const isDiagonal = rowIndex === colIndex;
                            const intensity = maxMatrixValue === 0 ? 0 : value / maxMatrixValue;
                            const textColor = intensity > 0.42 ? "#ffffff" : "#374151";
                            return (
                              <Box
                                key={`${actualLabel}-${predictedLabel}`}
                                component="td"
                                sx={{
                                  width: 64,
                                  height: 48,
                                  borderRadius: 1.2,
                                  textAlign: "center",
                                  fontSize: "0.85rem",
                                  fontWeight: isDiagonal ? 700 : 600,
                                  color: textColor,
                                  bgcolor: getMatrixCellBackground(value, maxMatrixValue, isDiagonal),
                                  boxShadow: isDiagonal ? "inset 0 0 0 1px rgba(109, 40, 217, 0.2)" : "none",
                                }}
                              >
                                {value}
                              </Box>
                            );
                          })}
                        </Box>
                      ))}
                    </Box>
                  </Box>
                  <Typography
                    variant="caption"
                    sx={{ display: "block", mt: 1.2, color: "#6b7280", textAlign: "center", fontWeight: 600 }}
                  >
                    Actual Label
                  </Typography>
                </Box>
              </Box>

              <Stack
                direction={{ xs: "column", sm: "row" }}
                spacing={1.5}
                sx={{ mt: 2 }}
              >
                <Box
                  sx={{
                    flex: 1,
                    borderRadius: 2,
                    border: "1px solid #e5e7eb",
                    bgcolor: "#fff",
                    px: 2,
                    py: 1.5,
                  }}
                >
                  <Typography variant="caption" sx={{ color: "#6b7280", fontWeight: 600 }}>
                    Precision
                  </Typography>
                  <Typography variant="h6" sx={{ mt: 0.3, color: "#111827", fontWeight: 700 }}>
                    {formatMetricValue(metrics.metrics.precision)}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    flex: 1,
                    borderRadius: 2,
                    border: "1px solid #e5e7eb",
                    bgcolor: "#fff",
                    px: 2,
                    py: 1.5,
                  }}
                >
                  <Typography variant="caption" sx={{ color: "#6b7280", fontWeight: 600 }}>
                    Recall
                  </Typography>
                  <Typography variant="h6" sx={{ mt: 0.3, color: "#111827", fontWeight: 700 }}>
                    {formatMetricValue(metrics.metrics.recall)}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    flex: 1,
                    borderRadius: 2,
                    border: "1px solid #e5e7eb",
                    bgcolor: "#fff",
                    px: 2,
                    py: 1.5,
                  }}
                >
                  <Typography variant="caption" sx={{ color: "#6b7280", fontWeight: 600 }}>
                    F1 Score
                  </Typography>
                  <Typography variant="h6" sx={{ mt: 0.3, color: "#111827", fontWeight: 700 }}>
                    {formatMetricValue(metrics.metrics.f1_score)}
                  </Typography>
                </Box>
              </Stack>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};
