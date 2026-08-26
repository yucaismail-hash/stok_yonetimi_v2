# Stokonomi Akademi Editoryal Yayın Standardı v1

Bu doküman, Stokonomi Akademi makalelerini Directus üzerinden hazırlayan içerik editörleri için operasyon standardıdır. Amaç; her makalenin aynı kalite, SEO ve yayın güvenliğiyle hazırlanmasıdır. Yeni CMS özelliği veya şema değişikliği tanımlamaz.

## 1. Mevcut içerik sözleşmesi

`academy_articles` koleksiyonunda kullanılan alanlar:

| Alan | Kullanım |
| --- | --- |
| `status` | `draft`, `published` veya `archived` yayın durumu |
| `sort` | Kart sırası için isteğe bağlı sayı |
| `slug` | Kalıcı makale URL'si; benzersizdir |
| `title` | Makale başlığı (sayfadaki H1) |
| `description` | Akademi kart açıklaması |
| `category` | Kontrollü kategori metni |
| `published_at` | Yayın zamanı |
| `updated_at` | Directus tarafından yönetilen son güncelleme zamanı |
| `reading_time` | Dakika cinsinden okuma süresi |
| `sections` | Makale gövdesi; desteklenen section dizisi |
| `seo_title` | İsteğe bağlı SEO başlığı |
| `seo_description` | İsteğe bağlı SEO açıklaması |
| `featured_image` | İsteğe bağlı Directus dosya ilişkisi |
| `featured_image_alt` | Görsel varsa anlamlı alternatif metin |

Mevcut read-only durum örneği: `emniyet-stoku-nedir` published; `stok-yonetimi-nedir`, `yeniden-siparis-noktasi-rop-nedir` ve `talep-tahmini-nedir` draft olarak yönetilmiştir. Bu durumlar bu standart kapsamında değiştirilmez.

## 2. Yayın durumu standardı

### Draft

- Hazırlık, editoryal kontrol ve SEO incelemesi durumudur.
- Public Content API, Akademi sayfaları ve sitemap içinde görünmez.
- Yeni makale her zaman `draft` olarak başlar.

### Published

- Yayınlanmış içeriktir.
- `published_at` girilmeden published yapılmaz.
- Public Content API, `/akademi`, makale sayfası, landing Academy alanı ve sitemap zincirine girer.

### Archived

- Yayından kaldırılmış içeriktir.
- Public API, Akademi listesi ve sitemap içinde görünmez.
- Mevcut public API davranışında archived URL, bilinmeyen veya draft içerik gibi 404 döner.

Geçiş kuralı: `draft → published` yalnız publish checklist tamamlanınca yapılır. Güncelleme gerekiyorsa makale yeniden `draft` incelemesine alınabilir; yayından kaldırma için `archived` kullanılır. Redirect ihtiyacı ayrı bir SEO kararıdır.

## 3. URL, sıra ve kategori

### Slug

- Küçük harf kullanın.
- Türkçe karakter kullanmayın (`ş` yerine `s`, `ı` yerine `i`).
- Boşluk yerine `-` kullanın.
- Yalnız `a-z`, `0-9` ve `-` kullanın.
- Slug kalıcı URL kabul edilir; yayın sonrası gereksiz değiştirilmez.
- Aynı slug tekrar kullanılamaz.

Örnekler: `emniyet-stoku-nedir`, `yeniden-siparis-noktasi-rop-nedir`.

### Sort

Varsayılan sıralama 10'ar artar: `10`, `20`, `30`, `40`, `50`. Araya içerik eklemek gerektiğinde `15` veya `25` kullanılabilir. Mevcut kayıtların `sort` alanını yalnız bu standardı uygulamak için değiştirmeyin.

### Category controlled vocabulary v1

- Temel Kavramlar
- Emniyet Stoku
- Operasyon
- Tahmin
- Stok Analizi
- Tedarik
- Simülasyon
- İleri Seviye

Frontend bugün Temel Kavramlar, Emniyet Stoku, Operasyon ve Tahmin için özel ikon kullanır. Stok Analizi, Tedarik, Simülasyon ve İleri Seviye güvenli varsayılan ikonla görünür. Özel ikon gereksinimi ayrı frontend mapping görevidir; bu standard kapsamında kategori değerleri değiştirilmez.

## 4. Metadata standardı

### Description

- 1–2 cümle, hedef olarak 120–180 karakter.
- Makalenin ne öğrettiğini açıkça söyler.
- Clickbait, keyword stuffing ve ürün satış metni kullanılmaz.

### SEO title

- Ana sorgu başta olmalıdır.
- Konu açık olmalıdır.
- Hedef uzunluk yaklaşık 50–65 karakterdir; kalite için bu aralık aşılabilir.
- Gerekirse `| Stokonomi` eklenir.

Örnek: `Emniyet Stoku Nedir? Hesaplama Yöntemleri ve Örnek | Stokonomi`.

### SEO description

- Hedef uzunluk yaklaşık 140–165 karakterdir.
- Okurun ne öğreneceğini ve ana kavramı doğal biçimde anlatır.
- CTA zorunlu değildir; keyword stuffing yapılmaz.

### Reading time

Tek yöntem kullanılır: `ceil(toplam gerçek içerik kelimesi / 180)`. En az 1 dakikadır. Sections içindeki gerçek metinler sayılır; rastgele okuma süresi girilmez.

## 5. Sections ve içerik yapısı

Desteklenen section type değerleri yalnız şunlardır:

`heading`, `paragraph`, `bulletList`, `numberedList`, `callout`, `formula`, `example`, `table`, `faq`, `divider`.

Yeni bir section tipi editör tarafından oluşturulmaz. Önerilen makale iskeleti: kısa giriş, neden önemli, temel kavramlar, yöntem/formül, örnek, uygulama, hatalar, ilişkili kavramlar, FAQ ve özet. Her makale tüm section türlerini kullanmak zorunda değildir.

### Heading

- Article title zaten H1'dir.
- Sections içinde ana bölüm için yalnız level 2, alt bölüm için yalnız level 3 kullanılır.
- Section içinde H1 kullanılmaz.

### Formula ve table

- Formula kısa ve okunabilir olmalıdır; değişkenler çevresindeki paragrafta açıklanır.
- Table mobilde okunabilir makul sayıda kolona sahip olmalıdır.
- Her satırdaki hücre sayısı header sayısıyla aynı olmalıdır.

### FAQ

- Sadece doğrudan ilgili sorular eklenir.
- İdeal sayı 3–6 sorudur.
- Cevaplar kısa ve doğrudandır; spam amacıyla üretilmez.
- FAQ bulunduğunda frontend ilgili FAQPage JSON-LD bilgisini üretir.

## 6. Featured image

Featured image şimdilik isteğe bağlıdır. Görsel eklenirse içerikle doğrudan ilgili ve marka standardına uygun olmalıdır. `featured_image_alt` zorunlu kabul edilir; görseli tanımlar, keyword stuffing içermez. Görsel yoksa mevcut default OG fallback kullanılır.

## 7. Publish checklist

- [ ] Slug doğru ve benzersiz.
- [ ] Title doğru.
- [ ] Description dolu ve standarda uygun.
- [ ] Category controlled vocabulary içinde.
- [ ] Sections geçerli type ve alanlarla hazırlanmış.
- [ ] Formüller kontrol edildi.
- [ ] Tablolar kontrol edildi.
- [ ] FAQ varsa geçerli.
- [ ] SEO title dolu.
- [ ] SEO description dolu.
- [ ] Reading time hesaplandı.
- [ ] Featured image varsa alt text var.
- [ ] Status hâlâ draft.
- [ ] Preview ve editoryal okuma tamamlandı.
- [ ] `published_at` girilecek.
- [ ] Status published yapılacak.

## 8. Post-publish checklist

- [ ] Akademi kartı `/akademi` içinde görünüyor.
- [ ] `/akademi/{slug}` açılıyor.
- [ ] Title, meta ve canonical doğru.
- [ ] Sitemap içinde makale URL'si var.
- [ ] Draft içerikler yanlışlıkla görünmüyor.

Normal operasyon için browser seviyesinde kısa kontrol yeterlidir. Teknik belirti varsa Content API ve sitemap smoke incelemesi yapılır.

## 9. Archive checklist

Archived yapıldıktan sonra makale public listeden, detay sayfasından ve sitemap'ten çıkmalıdır. Redirect gereksinimi varsa ayrı SEO kararı alınır; bu standart redirect sistemi tanımlamaz.

## 10. Editoryal SOP

`Fikir → Draft → İçerik İncelemesi → SEO İncelemesi → Publish → Post-Publish Check → Güncelleme / Archive`

1. Fikri controlled category ve kalıcı slug ile draft olarak açın.
2. Sections standardına uygun içeriği hazırlayın; reading time hesaplayın.
3. İçerik incelemesinde doğruluk, formül, tablo ve FAQ'ı kontrol edin.
4. SEO incelemesinde title, description, canonical slug ve varsa görsel alt metnini kontrol edin.
5. Publish checklist tamamlandığında `published_at` girin ve status'ü published yapın.
6. Browser üzerinden kart, makale URL'si ve sitemap görünürlüğünü kontrol edin.
7. Güncelleme için tekrar editoryal inceleme yapın; yayından kaldırmak için archived kullanın.
