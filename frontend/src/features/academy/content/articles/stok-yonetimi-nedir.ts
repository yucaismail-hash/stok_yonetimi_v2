// src/features/academy/content/articles/stok-yonetimi-nedir.ts
import { Article } from '../types';

export const article: Article = {
  slug: 'stok-yonetimi-nedir',
  title: 'Stok Yönetimi Nedir?',
  description:
    'Stok yönetiminin temel amaçlarını, maliyet ve hizmet seviyesi dengesiyle birlikte ele alan kapsamlı giriş rehberi.',
  category: 'Temel Kavramlar',
  publishedAt: '2026-01-15',
  updatedAt: '2026-01-15',
  readingTime: 8,
  status: 'published',
  sections: [
    {
      type: 'paragraph',
      content:
        'Stok yönetimi; bir işletmenin ihtiyaç duyduğu malzeme, ürün veya hammaddenin doğru zamanda, doğru yerde ve uygun miktarda bulunmasını sağlarken fazla stok ile stok yetersizliği arasındaki dengeyi yönetme sürecidir.',
    },
    {
      type: 'heading',
      level: 2,
      content: 'Stok Yönetimi Neden Önemlidir?',
    },
    {
      type: 'paragraph',
      content:
        'Stok yönetiminin önemi, işletmelerin karşılaştığı iki temel riskten kaynaklanır: fazla stok ve stok yetersizliği. Fazla stok sermayeyi bağlar, depolama maliyetini artırır ve ürünlerin eskime veya bozulma riskini büyütür. Stok yetersizliği ise satış kaybına, üretim kesintisine ve hizmet seviyesinin düşmesine neden olabilir.',
    },
    {
      type: 'paragraph',
      content:
        'Stok yönetiminin amacı "mümkün olan en az stok" değildir. Amaç, gereken hizmet seviyesini kabul edilebilir maliyet ve riskle sağlayacak stok seviyesini yönetmektir.',
    },
    {
      type: 'heading',
      level: 2,
      content: 'Stok Yönetiminin Temel Amaçları',
    },
    {
      type: 'bulletList',
      items: [
        'Doğru ürünü/malzemeyi bulundurmak',
        'Doğru miktarı belirlemek',
        'Doğru zamanda ikmal etmek',
        'Fazla stok maliyetini azaltmak',
        'Stok yetersizliği riskini azaltmak',
        'Nakit ve işletme sermayesini daha verimli kullanmak',
        'Hizmet seviyesini korumak',
      ],
    },
    {
      type: 'heading',
      level: 2,
      content: 'Stok Yönetimi Nasıl Yapılır?',
    },
    {
      type: 'paragraph',
      content:
        'Stok yönetimi, birbiriyle bağlantılı bir dizi adımdan oluşur. Bu adımlar, işletmenin ihtiyaçlarına ve veri olgunluğuna göre derinleşebilir veya sadeleşebilir.',
    },
    {
      type: 'numberedList',
      items: [
        'Talep verisini anlamak',
        'Talep davranışını analiz etmek',
        'Tedarik süresini değerlendirmek',
        'Emniyet stokunu belirlemek',
        'Yeniden sipariş noktasını belirlemek',
        'Sipariş miktarını planlamak',
        'Gerçekleşen sonuçları izlemek',
        'Tahminleri ve politikaları güncellemek',
      ],
    },
    {
      type: 'heading',
      level: 2,
      content: 'Basit Bir Stok Yönetimi Örneği',
    },
    {
      type: 'paragraph',
      content:
        'Bir hammaddenin ortalama haftalık tüketiminin 100 adet olduğunu varsayalım. Tedarik süresi 2 hafta ve emniyet stoku 50 adet olsun.',
    },
    {
      type: 'formula',
      content: 'Lead Time Demand = 100 × 2 = 200 adet',
    },
    {
      type: 'formula',
      content: 'ROP (Yeniden Sipariş Noktası) = 200 + 50 = 250 adet',
    },
    {
      type: 'example',
      content:
        'Stok pozisyonu yaklaşık 250 adede geldiğinde yeni sipariş değerlendirilir. Bu basitleştirilmiş bir örnektir. Gerçek hayatta talep değişkenliği, tedarik süresi değişkenliği, minimum sipariş miktarı, mevcut açık siparişler ve hizmet seviyesi gibi etkenler de hesaba katılır.',
    },
    {
      type: 'heading',
      level: 2,
      content: 'Stok Yönetiminde Temel Kavramlar',
    },
    {
      type: 'table',
      headers: ['Kavram', 'Ne Anlama Gelir?'],
      rows: [
        ['Talep Tahmini', 'Geçmiş veriden gelecekteki talebi öngörmeye çalışan analiz süreci.'],
        ['Emniyet Stoku', 'Talep ve tedarik belirsizliklerine karşı bulundurulan ek stok miktarı.'],
        ['Yeniden Sipariş Noktası (ROP)', 'Yeni sipariş verilmesi gereken stok seviyesi.'],
        ['Tedarik Süresi', 'Siparişin verilmesinden teslim alınmasına kadar geçen süre.'],
        ['Hizmet Seviyesi', 'Stok bulunmama riskine karşı belirlenen hedef oran.'],
        ['Stok Devir Hızı', 'Belirli bir dönemde stokun kaç kez yenilendiğini gösteren oran.'],
        ['ABC Analizi', 'Ürünleri değer ve önemlerine göre sınıflandıran yöntem.'],
        ['XYZ Analizi', 'Ürünleri talep düzenliliğine göre sınıflandıran yöntem.'],
      ],
    },
    {
      type: 'heading',
      level: 2,
      content: 'Stok Yönetiminde En Sık Yapılan Hatalar',
    },
    {
      type: 'bulletList',
      items: [
        'Sadece geçmiş ortalamaya güvenmek',
        'Tüm ürünlere aynı stok politikasını uygulamak',
        'Tedarik değişkenliğini görmezden gelmek',
        'Aşırı emniyet stoku kullanmak',
        'Stok yetersizliğini sadece satın alma problemi görmek',
        'Tahmin hatasını ölçmemek',
        'Gerçekleşen sonuçlardan öğrenmemek',
      ],
    },
    {
      type: 'heading',
      level: 2,
      content: 'Stok Yönetimi ve Belirsizlik',
    },
    {
      type: 'paragraph',
      content:
        'Stok yönetimi deterministik tek bir sayı problemi değildir. Talep değişebilir. Termin değişebilir. Tahmin hata içerebilir. Bu nedenle stok yönetimi, hesaplama ile başlayan, ölçüm, senaryo ve doğrulama ile devam eden bir süreçtir.',
    },
    {
      type: 'callout',
      content:
        'Stok yönetiminde asıl soru "ne kadar stok olmalı?" değil, "belirsizlik altında hangi stok seviyesi makul bir karardır?" sorusudur.',
    },
    {
      type: 'divider',
      content: '',
    },
    {
      type: 'faq',
      faqs: [
        {
          question: 'Stok yönetiminin temel amacı nedir?',
          answer:
            'Stok yönetiminin temel amacı, doğru ürünü doğru miktarda ve doğru zamanda bulundurarak fazla stok ile stok yetersizliği arasındaki dengeyi yönetmektir.',
        },
        {
          question: 'Fazla stok neden zararlıdır?',
          answer:
            'Fazla stok işletme sermayesini bağlar, depolama maliyetlerini artırır, ürünlerin eskime veya bozulma riskini büyütür ve nakit akışını olumsuz etkiler.',
        },
        {
          question: 'Stok yetersizliği neden oluşur?',
          answer:
            'Stok yetersizliği genellikle talebin beklenenden yüksek gelmesi, tedarik süresinin uzaması, tahmin hataları veya yetersiz emniyet stoku nedeniyle oluşur.',
        },
        {
          question: 'Emniyet stoku ile stok yönetimi arasındaki ilişki nedir?',
          answer:
            'Emniyet stoku, talep ve tedarik belirsizliklerine karşı bir tampon görevi görür. Stok yönetiminin önemli bir parçasıdır ve hizmet seviyesi ile doğrudan ilişkilidir.',
        },
        {
          question: 'Talep tahmini stok yönetiminde neden önemlidir?',
          answer:
            'Talep tahmini, sipariş miktarlarını ve zamanlamasını belirlemenin temelini oluşturur. Daha iyi tahminler, daha doğru stok seviyelerine yol açar.',
        },
        {
          question: 'Her ürün için aynı stok politikası kullanılabilir mi?',
          answer:
            'Hayır. ABC analizi gibi yöntemlerle ürünler değer ve önemlerine göre sınıflandırılmalı, her kategori için farklı bir stok politikası belirlenmelidir.',
        },
      ],
    },
  ],
};