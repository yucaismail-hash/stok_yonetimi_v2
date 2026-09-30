# DIRECTUS-D2 Academy content contract

## CURRENT closeout

D2, yalnız backend Academy content okuma sözleşmesini sertleştirir. Şema, medya
teslimi, SSR/prerender ve Production erişimi bu fazın dışındadır.

Kanonik public uygunluk:

`status == published AND published_at IS NOT NULL AND published_at <= governed_time`

`governed_time` her servis çağrısında bir kez alınan timezone-aware UTC andır.
İstemci aynı anı Directus liste ve detay filtrelerine gönderir; istemci ve servis
dönen DTO'ları aynı predicate ile yeniden doğrular. Timestamp timezone bilgisi
taşımıyorsa payload geçersizdir. Eşitlik (`published_at == governed_time`) yayın
için uygundur; gelecekteki içerik uygun değildir.

## Pagination ve sıralama

- Varsayılan sayfa boyutu 50, izin verilen aralık 1–100'dür.
- Her istek açık `limit` ve birden başlayan `page` taşır.
- Sıra `-published_at,sort,id` olup benzersiz `id` son tie-breaker'dır.
- Kısa/boş sayfaya kadar devam edilir; Directus varsayılan limiti kullanılmaz.
- Sayfalar arasında duplicate `id` veya `slug` sözleşme ihlalidir ve tüm çağrıyı
  fail closed yapar. Sessiz deduplication yoktur.

## Malformed içerik kararı

CURRENT D1 davranışı önce regresyon testiyle yeniden üretildi: listede bir geçerli
ve bir malformed kayıt varsa DTO doğrulaması tüm listeyi başarısız yapar. D2'nin
kanonik kararı **whole-list fail closed** seçeneğidir. Malformed kayıt sessizce
atlanmaz; public liste ve sitemap güvenli 502 döndürür. Bu, eksik içeriği başarılı
yanıt gibi göstermeden operasyonel olarak görünür kılar.

## Liste, detay ve sitemap eşitliği

Liste ve detay aynı Directus predicate'i ve aynı uygulama savunmasını kullanır.
Sitemap ayrı sorgu yapmaz; kanonik servis listesinin tamamını kullanır. `lastmod`
önce `updated_at`, yoksa `published_at` kaynağından üretilir. Böylece draft,
archived, null-published ve future-published kayıt üç yüzeyde de public değildir.

## Kanıt ve sınırlar

Unit/regression matrisi filtre parametrelerini, eşit/future sınırını, timezone
reddini, çoklu sayfayı, duplicate korumasını, malformed whole-list hatasını ve
sitemap hata eşlemesini kapsar. D1 disposable reconstruction testi iki kayıtlık
sayfayla üç uygun synthetic kayıt, draft kayıt ve future-published kayıt kullanır.

Production erişimi ve mutation yapılmamıştır. D3 medya/R2, D4 SSR/prerender ve D5
Production service-token/policy assignment ayrı TARGET fazlarıdır.
