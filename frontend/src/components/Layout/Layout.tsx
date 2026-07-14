import { Outlet, Navigate } from 'react-router-dom';
import { Box, Toolbar } from '@mui/material';
import { useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import Footer from './Footer';

const drawerWidth = 260;

export default function Layout() {
  const { user, isLoading } = useAuth();

  // ✅ SEO: Sayfa başlığını ve meta etiketleri güncelle
  useEffect(() => {
    // Sayfa başlığını güncelle
    document.title = 'Stokonomi - Stok Yönetim Sistemi';
    
    // Meta description'ı güncelle
    let metaDescription = document.querySelector('meta[name="description"]');
    if (!metaDescription) {
      metaDescription = document.createElement('meta');
      metaDescription.setAttribute('name', 'description');
      document.head.appendChild(metaDescription);
    }
    metaDescription.setAttribute('content', 'Stokonomi ile stok yönetimini optimize edin, talep tahmini yapın, emniyet stoku hesaplayın ve tedarik zincirinizi yönetin.');
    
    // Open Graph meta etiketlerini güncelle
    let ogTitle = document.querySelector('meta[property="og:title"]');
    if (!ogTitle) {
      ogTitle = document.createElement('meta');
      ogTitle.setAttribute('property', 'og:title');
      document.head.appendChild(ogTitle);
    }
    ogTitle.setAttribute('content', 'Stokonomi - Stok Yönetim Sistemi');
    
    let ogDescription = document.querySelector('meta[property="og:description"]');
    if (!ogDescription) {
      ogDescription = document.createElement('meta');
      ogDescription.setAttribute('property', 'og:description');
      document.head.appendChild(ogDescription);
    }
    ogDescription.setAttribute('content', 'Stokonomi ile stok yönetimini optimize edin, talep tahmini yapın, emniyet stoku hesaplayın ve tedarik zincirinizi yönetin.');
  }, []);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        Yükleniyor...
      </Box>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <Navbar drawerWidth={drawerWidth} />
      <Sidebar drawerWidth={drawerWidth} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          backgroundColor: '#f8faff',
          display: "flex",
          flexDirection: "column",
          minHeight: '100vh',
        }}
      >
        <Toolbar />
        <Outlet />
        <Footer />
      </Box>
    </Box>
  );
}