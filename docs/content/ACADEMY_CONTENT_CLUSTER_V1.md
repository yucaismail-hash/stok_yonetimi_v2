# Stokonomi Akademi Content Cluster v1

Bu doküman P8A için ilk Akademi pillar/cluster planıdır. Yeni içerik oluşturmaz, Directus kayıtlarını değiştirmez ve keyword volume iddiasında bulunmaz.

## 1. Mevcut içerik inventory

| Slug | Durum | Başlık | Category / sort | Metadata durumu |
| --- | --- | --- | --- | --- |
| `stok-yonetimi-nedir` | draft | Stok Yönetimi Nedir? | Directus read-only teyidi bekliyor | `published_at` draft için boş; description ve SEO alanları CMS kaynağıdır |
| `emniyet-stoku-nedir` | published | Emniyet Stoku Nedir? | Directus read-only teyidi bekliyor | Public zincirde görünen örnek; exact description/SEO CMS kaynağından korunur |
| `yeniden-siparis-noktasi-rop-nedir` | draft | Yeniden Sipariş Noktası (ROP) Nedir? | Directus read-only teyidi bekliyor | `published_at` draft için boş |
| `talep-tahmini-nedir` | draft | Talep Tahmini Nedir? | Directus read-only teyidi bekliyor | `published_at` draft için boş |
| `abc-analizi-nedir` | Directus read-only teyidi bekliyor | ABC Analizi Nedir? | Directus read-only teyidi bekliyor | Bu P8A brief'inde mevcut içerik olarak belirtilmiştir; alan değerleri tahmin edilmez |

P8A çalışması sırasında public inventory endpoint’i erişilemedi ve repoda CMS editör token’ı bulunmuyor. Bu nedenle status, category, sort, description, SEO title ve SEO description alanlarının güncel değerleri uydurulmamıştır. P8B öncesinde Directus admin üzerinden salt-okunur inventory kontrolü yapılmalıdır.

## 2. Primary pillar: Stok Yönetimi

İlk pillar **Stok Yönetimi**dir. `stok-yonetimi-nedir` makalesi pillar giriş içeriği olarak konumlanır: okuyucuya temel tanımı verir ve aşağıdaki uzmanlaşmış kavramlara yönlendirir. Yeni pillar page, route veya schema gerekmemektedir.

## 3. Cluster v1

```text
Stok Yönetimi Nedir? (pillar)
├─ ABC Analizi Nedir?
├─ Stok Devir Hızı Nedir?
├─ Stokout Nedir?
├─ Fazla Stok Nedir?                         [sonraki dalga]
├─ Stok Maliyeti Nedir?                      [sonraki dalga]
├─ Emniyet Stoku Nedir?
│  ├─ Servis Seviyesi Nedir?
│  ├─ Lead Time Nedir?
│  └─ Yeniden Sipariş Noktası (ROP) Nedir?
│     └─ Ekonomik Sipariş Miktarı (EOQ) Nedir?
└─ Talep Tahmini Nedir?
   ├─ XYZ Analizi Nedir?                     [sonraki dalga]
   └─ ABC-XYZ Analizi Nedir?                 [sonraki dalga]
```

Supplier sadece uygun dataset olduğunda workflow grafiğine girer; Academy cluster'ında bu ürün davranışı ayrı bir SEO konusu olarak kullanılmaz.

## 4. Aday öncelik skoru

Skorlar 1–5 arasındadır. “Search intent / SEO değeri” göreli kullanıcı sorusu netliğidir; keyword hacmi değildir.

| Aday | Intent / SEO | Ürün yakınlığı | Internal link | Marketing reuse | Teknik açıklanabilirlik | İlk kullanıcı eğitimi | Toplam |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Stok Devir Hızı | 5 | 4 | 5 | 5 | 5 | 5 | 29 |
| Lead Time | 4 | 5 | 5 | 4 | 5 | 5 | 28 |
| Stokout | 4 | 5 | 5 | 5 | 4 | 5 | 28 |
| Servis Seviyesi | 4 | 5 | 5 | 4 | 4 | 5 | 27 |
| EOQ | 4 | 4 | 4 | 4 | 5 | 4 | 25 |
| Min-Max Stok Sistemi | 4 | 4 | 4 | 4 | 4 | 4 | 24 |
| Fazla Stok | 4 | 4 | 5 | 4 | 4 | 4 | 25 |
| XYZ Analizi | 3 | 4 | 5 | 3 | 4 | 4 | 23 |
| ABC-XYZ Analizi | 3 | 4 | 5 | 3 | 4 | 3 | 22 |
| Stok Maliyeti | 4 | 4 | 4 | 4 | 4 | 4 | 24 |

## 5. P8B ilk içerik batch'i

Önerilen sırada şu beş makale hazırlanır:

1. **Stok Devir Hızı Nedir?** — pillar ile maliyet/fazla stok konularını bağlayan güçlü temel kavram.
2. **Lead Time Nedir?** — ROP ve emniyet stoğu arasındaki kritik bağı açıklar.
3. **Servis Seviyesi Nedir?** — emniyet stoku kararının hedefini açıklar.
4. **Stokout Nedir?** — service level, emniyet stoğu ve müşteri etkisini bağlar.
5. **Ekonomik Sipariş Miktarı (EOQ) Nedir?** — ROP'tan farklı sipariş büyüklüğü kararını öğretir.

Bu sıra, yalnız genel kavram üretmek yerine mevcut ROP, Emniyet Stoku ve Talep Tahmini içerikleri arasındaki öğrenme yolunu önce tamamlar.

## 6. Slug, category ve sort planı

| Başlık | Canonical slug | Category | Sort yaklaşımı |
| --- | --- | --- | --- |
| Stok Devir Hızı Nedir? | `stok-devir-hizi-nedir` | Stok Analizi | Mevcut pillar/ABC sıralarını okuduktan sonra ilk boş 10'lu slot |
| Lead Time Nedir? | `lead-time-nedir` | Operasyon | ROP ve Emniyet Stoku yakınında ilk boş slot |
| Servis Seviyesi Nedir? | `servis-seviyesi-nedir` | Emniyet Stoku | Emniyet Stoku yakınında ilk boş slot |
| Stokout Nedir? | `stokout-nedir` | Operasyon | Servis Seviyesi/Emniyet Stoku kümesine yakın ilk boş slot |
| Ekonomik Sipariş Miktarı (EOQ) Nedir? | `ekonomik-siparis-miktari-eoq-nedir` | Operasyon | ROP yakınında ilk boş slot |

P7'nin 10'ar artan sort standardı uygulanır. Exact mevcut sort değerleri P8A read-only inventory sırasında doğrulanamadığından çakışma yaratacak sayı önerilmez. P8B create öncesi her slug için duplicate kontrolü ve sort için mevcut değer kontrolü zorunludur.

## 7. Internal link graph

| Kaynak içerik | İlgili içerik ve bağlam |
| --- | --- |
| Stok Yönetimi Nedir? | ABC Analizi, Stok Devir Hızı, Stokout, Emniyet Stoku, ROP, Talep Tahmini |
| ABC Analizi | Stok Devir Hızı; sonraki dalgada XYZ ve ABC-XYZ |
| Stok Devir Hızı | Stok Yönetimi, Fazla Stok, Stok Maliyeti, Stokout |
| Emniyet Stoku | Servis Seviyesi, Lead Time, ROP, Talep Tahmini |
| Lead Time | ROP, Emniyet Stoku, EOQ |
| Servis Seviyesi | Emniyet Stoku, Stokout, Talep Tahmini |
| ROP | Lead Time, Emniyet Stoku, EOQ |
| EOQ | ROP, Lead Time, Stok Maliyeti |
| Talep Tahmini | Emniyet Stoku, Servis Seviyesi; sonraki dalgada XYZ |
| Stokout | Servis Seviyesi, Emniyet Stoku, Stok Devir Hızı |

İç bağlantılar yalnız ilgili kavram makaleleri published olduğunda eklenir. P8B'de yayınlanmamış hedefe public link eklenmez.

## 8. İlk beş içerik intent ve blueprint'i

| İçerik | Birincil kullanıcı sorusu | Intent | Ana kavram | Formula/example | İlgili mevcut içerik | LinkedIn açısı |
| --- | --- | --- | --- | --- | --- | --- |
| Stok Devir Hızı | “Stok devir hızını nasıl yorumlarım?” | Bilgilendirici / hesaplama | Stok tüketim hızı ile ortalama stok ilişkisi | Formül ve sayısal örnek gerekli | Stok Yönetimi, ABC | “Stok devir hızınız yüksek diye her zaman iyi durumda olmayabilirsiniz.” |
| Lead Time | “Lead time stok seviyemi neden etkiler?” | Bilgilendirici / operasyonel | Teslim süresi belirsizliği | Zaman çizelgesi ve örnek gerekli | ROP, Emniyet Stoku | “Emniyet stokunun yarısı aslında lead time problemidir.” |
| Servis Seviyesi | “Hangi servis seviyesi hedeflenmeli?” | Bilgilendirici / karar desteği | Karşılama hedefi ve maliyet dengesi | Kısa örnek gerekli; zor formül şart değil | Emniyet Stoku, Stokout | “%99 servis seviyesi her ürün için doğru hedef değildir.” |
| Stokout | “Stokout nedir ve nasıl önlenir?” | Bilgilendirici / problem çözme | Stok tükenmesinin operasyonel etkisi | Senaryo örneği gerekli | Emniyet Stoku, Servis Seviyesi | “Stokout sadece satış kaybı değildir; planlama sinyalidir.” |
| EOQ | “EOQ neyi optimize eder?” | Bilgilendirici / hesaplama | Sipariş maliyeti ve taşıma maliyeti dengesi | Formül ve sayısal örnek gerekli | ROP, Lead Time | “En ucuz sipariş miktarı her zaman en doğru stok kararı değildir.” |

Her içerik P7 blueprint'ini izler: kısa cevap, neden önemli, temel bileşenler, gerekiyorsa formül/yöntem, sayısal örnek, uygulama, sık hata, ilgili kavramlar, FAQ ve özet.

## 9. Cannibalization sınırları

| Birbirine yakın konular | Ayrım |
| --- | --- |
| ROP / EOQ | ROP **ne zaman** sipariş verileceğini; EOQ **ne kadar** sipariş verileceğini anlatır. |
| Emniyet Stoku / Servis Seviyesi | Emniyet stoku tampon envanterdir; servis seviyesi hedeflenen karşılama sonucudur. |
| Talep Tahmini / XYZ | Tahmin gelecekteki talebi öngörür; XYZ talep değişkenliğini sınıflandırır. |
| Stok Yönetimi / Stok Maliyeti | Stok Yönetimi umbrella kavramdır; Stok Maliyeti taşıma, sipariş ve yok satma maliyetine odaklanır. |
| ABC / ABC-XYZ | ABC değer/önem sınıflaması; ABC-XYZ değer ile talep değişkenliğini birlikte sınıflar. |
| Stok Devir Hızı / Stokout | Devir hızı hareket verimliliği; stokout ise hizmette kesinti olayıdır. |

## 10. P8B create gate

P8B başlamadan önce:

1. Directus'tan beş mevcut kaydın exact inventory alanları salt-okunur doğrulanır.
2. Planlanan slug'lar için duplicate kontrolü yapılır.
3. Mevcut `sort` değerlerine göre boş 10'lu veya ara slot seçilir.
4. İlk beş içerik yalnız draft olarak oluşturulur; publish ayrı kontrollü adımdır.
