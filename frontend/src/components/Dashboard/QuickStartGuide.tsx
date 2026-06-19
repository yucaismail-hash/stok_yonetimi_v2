import { Card, CardContent, Typography, Button, Box, Stepper, Step, StepLabel } from '@mui/material';

export default function QuickStartGuide() {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
          🚀 Başlangıç Rehberi
        </Typography>
        <Stepper activeStep={0} orientation="vertical">
          <Step>
            <StepLabel>1. Excel dosyasını yükleyin</StepLabel>
          </Step>
          <Step>
            <StepLabel>2. Pattern analizini çalıştırın</StepLabel>
          </Step>
          <Step>
            <StepLabel>3. Safety Stock hesaplatın</StepLabel>
          </Step>
          <Step>
            <StepLabel>4. Raporu alın</StepLabel>
          </Step>
        </Stepper>
        <Box sx={{ mt: 2 }}>
          <Button variant="contained" size="small" href="/upload">
            Hemen Başla
          </Button>
          <Button variant="outlined" size="small" sx={{ ml: 1 }} href="/docs">
            Dokümantasyon
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}