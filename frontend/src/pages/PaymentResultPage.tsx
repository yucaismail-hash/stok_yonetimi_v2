// frontend/src/pages/PaymentResultPage.tsx
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function PaymentResultPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { fetchUser } = useAuth();
  const checkoutId = searchParams.get('checkout_id');
  const sessionToken = searchParams.get('customer_session_token');

  useEffect(() => {
    const handlePayment = async () => {
      // Sayfa yüklendiğinde, eğer checkout_id varsa işlemi tamamla
      if (checkoutId) {
        console.log('🔍 [DEBUG] PaymentResult: checkout_id bulundu:', checkoutId);
        
        // Kullanıcı bilgilerini yenile (kredi bakiyesi güncellenir)
        await fetchUser();
        
        // Başarılı mesajı ve durumu ile Dashboard'a yönlendir
        navigate('/dashboard', { 
          state: { 
            paymentStatus: 'success',
            paymentMessage: 'Kredileriniz başarıyla eklendi!',
            checkoutId: checkoutId
          } 
        });
      } else {
        // Eğer checkout_id yoksa (belki iptal veya hatalı dönüş), ana sayfaya yönlendir
        navigate('/dashboard');
      }
    };

    handlePayment();
  }, [checkoutId, navigate, fetchUser]);

  // Bu sayfa sadece bir geçiş sayfası olduğu için boş veya basit bir yüklenme animasyonu gösterilebilir.
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh' 
    }}>
      <p>Ödeme sonucu işleniyor, yönlendiriliyorsunuz...</p>
    </div>
  );
}