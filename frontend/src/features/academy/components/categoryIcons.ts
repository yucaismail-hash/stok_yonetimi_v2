import {
  Analytics as AnalyticsIcon,
  MenuBook as DefaultCategoryIcon,
  School as SchoolIcon,
  Security as SecurityIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import type { SvgIconComponent } from '@mui/icons-material';

const CATEGORY_ICONS: Record<string, SvgIconComponent> = {
  'Temel Kavramlar': SchoolIcon,
  'Emniyet Stoku': SecurityIcon,
  Operasyon: TimelineIcon,
  Tahmin: AnalyticsIcon,
};

export function getAcademyCategoryIcon(category: string): SvgIconComponent {
  return CATEGORY_ICONS[category] ?? DefaultCategoryIcon;
}
