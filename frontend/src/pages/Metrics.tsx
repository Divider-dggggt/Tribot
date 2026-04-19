import { useEffect, useState, type ReactElement } from "react";
import { API_BASE_URL } from "../utils/constants";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import { fetchWithAuth } from "../utils/auth";
import { CircularProgress } from "@mui/material";
// @ts-ignore no type declaration available
import { ConfusionMatrix } from "react-confusion-matrix";

interface ModelMetricsAPIResponse {
  model_name: string;
  metrics: {
    f1_score: number;
    precision: number;
    recall: number;
    confusion_matrix: number[][];
  };
}

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
          {isLoading && <Box 
            display="flex"
            justifyContent="center"
            alignItems="center"
            sx={{ p: 4 }}
          >
            <CircularProgress />
          </Box>}
          {!isLoading && metrics != null && <Box sx={{ px: 3, py: 2.5, borderBottom: "1px solid #e5e7eb" }}>
            <Typography variant="h6" fontWeight="bold">
              Confusion Matrix
            </Typography>
            <ConfusionMatrix data={metrics.metrics.confusion_matrix} labels={["ATS-1", "ATS-2", "ATS-3", "ATS-4", "ATS-5"]} />
            <Typography>
              Precision: {metrics.metrics.precision}
            </Typography>
            <Typography>
              Recall: {metrics.metrics.recall}
            </Typography>
            <Typography>
              F1 Score: {metrics.metrics.f1_score}
            </Typography>
          </Box>}
        </CardContent>
      </Card>
    </Box>
  );
};
