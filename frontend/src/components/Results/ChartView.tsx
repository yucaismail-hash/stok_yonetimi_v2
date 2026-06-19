import {
  Card,
  CardContent,
  Typography,
  Box,
  useTheme,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface ChartViewProps {
  type: 'forecast' | 'simulation' | 'backtest' | 'pattern';
  data: any;
  title?: string;
}

// Tip tanımları
interface ForecastData {
  mean: number[];
  lower_95: number[];
  upper_95: number[];
  lower_80: number[];
  upper_80: number[];
}

interface SimulationData {
  stockout_probability: number[];
  expected_shortage: number[];
  avg_stock: number[];
}

interface BacktestData {
  comparison: {
    service_level: Record<string, number>;
    total_cost: Record<string, number>;
  };
}

interface PatternData {
  weekly_data: number[];
}

export default function ChartView({ type, data, title }: ChartViewProps) {
  const theme = useTheme();

  const renderForecastChart = () => {
    if (!data?.mean) return null;

    const chartData = data.mean.map((value: number, index: number) => ({
      week: index + 1,
      mean: value,
      lower_95: data.lower_95?.[index] || 0,
      upper_95: data.upper_95?.[index] || 0,
      lower_80: data.lower_80?.[index] || 0,
      upper_80: data.upper_80?.[index] || 0,
    }));

    return (
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="week" label={{ value: 'Hafta', position: 'bottom' }} />
          <YAxis label={{ value: 'Talep', angle: -90, position: 'left' }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="mean" stroke={theme.palette.primary.main} name="Tahmin" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="upper_95" stroke={theme.palette.error.light} name="%95 Üst" strokeDasharray="5 5" strokeWidth={1.5} dot={false} />
          <Line type="monotone" dataKey="lower_95" stroke={theme.palette.error.light} name="%95 Alt" strokeDasharray="5 5" strokeWidth={1.5} dot={false} />
          <Line type="monotone" dataKey="upper_80" stroke={theme.palette.warning.light} name="%80 Üst" strokeDasharray="3 3" strokeWidth={1} dot={false} />
          <Line type="monotone" dataKey="lower_80" stroke={theme.palette.warning.light} name="%80 Alt" strokeDasharray="3 3" strokeWidth={1} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  const renderSimulationChart = () => {
    if (!data?.stockout_probability) return null;

    const chartData = data.stockout_probability.map((value: number, index: number) => ({
      week: index + 1,
      stockout: value * 100,
      expected_shortage: data.expected_shortage?.[index] || 0,
      avg_stock: data.avg_stock?.[index] || 0,
    }));

    return (
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="week" label={{ value: 'Hafta', position: 'bottom' }} />
          <YAxis yAxisId="left" label={{ value: 'Stok Tükenme (%)', angle: -90, position: 'left' }} />
          <YAxis yAxisId="right" orientation="right" label={{ value: 'Miktar', angle: 90, position: 'right' }} />
          <Tooltip />
          <Legend />
          <Line yAxisId="left" type="monotone" dataKey="stockout" stroke={theme.palette.error.main} name="Stok Tükenme Olasılığı (%)" strokeWidth={2} />
          <Line yAxisId="right" type="monotone" dataKey="avg_stock" stroke={theme.palette.success.main} name="Ortalama Stok" strokeWidth={2} />
          <Line yAxisId="right" type="monotone" dataKey="expected_shortage" stroke={theme.palette.warning.main} name="Beklenen Açık" strokeWidth={2} strokeDasharray="3 3" />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  const renderBacktestChart = () => {
    if (!data?.comparison?.service_level) return null;

    const strategies = Object.keys(data.comparison.service_level);
    const chartData = strategies.map((key: string) => ({
      name: key,
      serviceLevel: data.comparison.service_level[key] * 100,
      totalCost: data.comparison.total_cost[key] / 1000,
    }));

    const COLORS = ['#1f4e79', '#2e7d32', '#ed6c02', '#9c27b0', '#d32f2f', '#1976d2', '#388e3c', '#f57c00'];

    return (
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Servis Seviyesi Karşılaştırması
        </Typography>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 100]} />
            <YAxis type="category" dataKey="name" width={100} />
            <Tooltip />
            <Bar dataKey="serviceLevel" fill={theme.palette.primary.main}>
              {chartData.map((entry: { name: string; serviceLevel: number; totalCost: number }, index: number) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
          Toplam Maliyet Karşılaştırması (bin TL)
        </Typography>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis type="category" dataKey="name" width={100} />
            <Tooltip />
            <Bar dataKey="totalCost" fill={theme.palette.success.main}>
              {chartData.map((entry: { name: string; serviceLevel: number; totalCost: number }, index: number) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Box>
    );
  };

  const renderPatternChart = () => {
    if (!data?.weekly_data) return null;

    const chartData = data.weekly_data.map((value: number, index: number) => ({
      week: index + 1,
      demand: value,
    }));

    return (
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="week" label={{ value: 'Hafta', position: 'bottom' }} />
          <YAxis label={{ value: 'Talep', angle: -90, position: 'left' }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="demand" fill={theme.palette.primary.main}>
            {chartData.map((entry: { week: number; demand: number }, index: number) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.demand === 0 ? theme.palette.error.light : theme.palette.primary.main} 
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const getChart = () => {
    switch (type) {
      case 'forecast':
        return renderForecastChart();
      case 'simulation':
        return renderSimulationChart();
      case 'backtest':
        return renderBacktestChart();
      case 'pattern':
        return renderPatternChart();
      default:
        return (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography color="text.secondary">Grafik verisi bulunamadı</Typography>
          </Box>
        );
    }
  };

  return (
    <Card>
      <CardContent>
        {title && (
          <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
            {title}
          </Typography>
        )}
        {getChart()}
      </CardContent>
    </Card>
  );
}