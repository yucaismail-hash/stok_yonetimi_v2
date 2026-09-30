# Stokonomi Directus deployment

Bu klasör yalnız Stokonomi içerik platformunun deployment tanımını içerir. Directus;
Akademi, içerik, medya ve SEO için kullanılacaktır. Ana operasyon veritabanına veya
operasyon servislerine bağlanmamalıdır.

## Sabitlenen image

`Dockerfile`, resmi `directus/directus:12.2.0` image'ını kullanır. `latest`, major
veya minor hareketli tag kullanmayın. Sürüm yükseltmeden önce Directus release
notlarını okuyun, `stokonomi_content` için geri dönüş noktası oluşturun ve yükseltmeyi
ayrı olarak doğrulayın. Directus container başlangıcında gerekli veritabanı
migration'larını uygulayabileceği için image sürümü kendiliğinden yükseltilmemelidir.

## Güvenlik sınırı

- `DB_CONNECTION_STRING` yalnız Neon `stokonomi_content` database'inin **direct
  (non-pooled)** bağlantısı olmalıdır.
- Ana operasyon database URL'sini bu servise vermeyin.
- Yerel `DATABASE_URL_CONTENT` değerini kaynak dosyalara kopyalamayın.
- Database credential, `SECRET`, admin parolası ve object-storage credential'ları
  yalnız Render secret environment variables olarak saklanmalıdır.
- Database credential veya admin token'ı hiçbir `VITE_*` değişkenine koymayın.
- Frontend'e Directus admin/static token vermeyin.
- `.env.example` yalnız sözleşme örneğidir; gerçek secret içermez.

## Render Web Service kurulumu

1. Render'da mevcut backend ve frontend'den bağımsız yeni bir **Web Service**
   oluşturun.
2. Aynı repository'yi bağlayın ve runtime olarak Docker seçin.
3. Dockerfile path değerini `directus/Dockerfile` olarak ayarlayın. Build context
   repository root olabilir; Dockerfile uygulama dosyası kopyalamaz.
4. İlk deployment'tan önce Neon'da `stokonomi_content` için snapshot veya branch
   biçiminde geri dönüş noktası oluşturun.
5. Neon dashboard'dan `stokonomi_content` database'ine ait **direct** connection
   URL'sini alın. Host adında pooler göstergesi bulunan pooled URL kullanmayın.
6. Direct URL'yi Render servisinin Environment bölümünde secret
   `DB_CONNECTION_STRING` olarak elle girin. Yerel `DATABASE_URL_CONTENT`, Directus
   tarafından otomatik okunmaz; bu değer Render'a kaynak kod üzerinden aktarılmaz.
7. `.env.example` içindeki diğer değişkenleri Render Environment bölümünde tanımlayın.
   Boş placeholder değerlerini aynen bırakmayın.
8. İlk URL belli olduğunda `PUBLIC_URL` değerini servisin tam HTTPS Render URL'si
   yapın. `cms.stokonomi.com` doğrulanıp servise bağlandıktan sonra `PUBLIC_URL`yi
   `https://cms.stokonomi.com` olarak değiştirin.
9. CURRENT Render HTTP health check path değeri `/server/ping`'dir. Bu ayar
   production dashboard-owned durumdadır; repository local reconstruction
   ortamı da aynı read-only ping endpoint'ini kullanır.
10. Servisi ilk kez tek instance ile açın. İlk başlangıç Directus sistem tablolarını
    kurabilir; log ve health sonucunu kontrol etmeden ikinci instance açmayın.
11. İlk admin girişi ve health kontrolü başarıyla tamamlandıktan sonra
    `ADMIN_EMAIL` ve `ADMIN_PASSWORD` değişkenlerini Render ortamından kaldırın.
    Kalıcı `ADMIN_TOKEN` oluşturmayın.
12. `academy_articles`, roller ve public permissions sonraki kontrollü adımda
    oluşturulmalıdır. Bu deployment hazırlığı bunları otomatik oluşturmaz.

## Environment değişkenleri

### Zorunlu runtime

| Değişken | Amaç | Secret |
| --- | --- | --- |
| `SECRET` | Directus token ve cookie imzalama anahtarı | Evet |
| `DB_CLIENT` | PostgreSQL driver; `pg` | Hayır |
| `DB_CONNECTION_STRING` | Neon `stokonomi_content` direct URL | Evet |
| `PUBLIC_URL` | Directus public canonical URL | Hayır |
| `PORT` | HTTP dinleme portu | Hayır |

Render çalışma anında `PORT` sağlıyorsa platform değerini kullanın. Elle tanımlamak
gerekirse servis ayarı ile aynı portu kullanın; Dockerfile image'ın varsayılan 8055
portunu expose eder.

### İlk bootstrap

| Değişken | Amaç | Secret |
| --- | --- | --- |
| `ADMIN_EMAIL` | İlk Super Admin hesabı | Hassas |
| `ADMIN_PASSWORD` | İlk Super Admin parolası | Evet |

Bu iki değişken yalnız ilk başarılı kurulum içindir ve sonrasında kaldırılmalıdır.

### CORS ve API koruması

| Değişken | Amaç |
| --- | --- |
| `CORS_ENABLED` | İzinli browser origin'lerinden erişim |
| `CORS_ORIGIN` | Stokonomi production ve gerekli local origin allowlist'i |
| `CORS_CREDENTIALS` | Public Academy API için `false` |
| `RATE_LIMITER_ENABLED` | Public API rate limiting |
| `RATE_LIMITER_POINTS` | Süre içindeki istek bütçesi |
| `RATE_LIMITER_DURATION` | Rate-limit zaman penceresi |
| `WEBSOCKETS_ENABLED` | İlk sürümde gerekli değil; `false` |
| `TELEMETRY` | Telemetry tercihi |
| `LOG_LEVEL` | Production log seviyesi |

`CORS_ORIGIN` değerini gerçek frontend origin'leriyle sınırlandırın. Preview origin'leri
gerekirse açıkça ekleyin; wildcard kullanmayın. CORS, Directus permissions yerine
geçmez.

## Kalıcı medya storage

Render container filesystem'i ephemeral olduğu için production upload'ları local
`/directus/uploads` altında tutulmamalıdır. İlk production içerik yüklemesinden önce
S3 uyumlu kalıcı object storage hazırlanmalıdır.

Gerekli bilgiler:

- storage provider ve endpoint
- bucket adı
- region
- access key ve secret
- provider'ın path-style gereksinimi
- server-side encryption seçeneği
- bucket CORS/lifecycle/backup politikası

Render secret/environment eşlemesi:

| Değişken | Amaç | Secret |
| --- | --- | --- |
| `STORAGE_LOCATIONS` | `media` storage location'ını etkinleştirir | Hayır |
| `STORAGE_MEDIA_DRIVER` | S3 driver | Hayır |
| `STORAGE_MEDIA_KEY` | Object-storage access key | Evet |
| `STORAGE_MEDIA_SECRET` | Object-storage secret | Evet |
| `STORAGE_MEDIA_BUCKET` | Bucket adı | Genellikle hayır |
| `STORAGE_MEDIA_REGION` | Bucket region | Hayır |
| `STORAGE_MEDIA_ENDPOINT` | S3 uyumlu endpoint | Hayır |
| `STORAGE_MEDIA_FORCE_PATH_STYLE` | Provider uyumluluk ayarı | Hayır |
| `STORAGE_MEDIA_SERVER_SIDE_ENCRYPTION` | Provider destekliyorsa encryption modu | Hayır |

Bucket'ı sırf frontend erişimi için public yapmayın. Medyanın Directus `/assets`
endpoint'i ve Directus file permissions üzerinden sunulması hedeflenir.

## Bu klasörün yapmadıkları

- Directus'u çalıştırmaz veya deploy etmez.
- Database bootstrap/migration çalıştırmaz.
- `academy_articles` koleksiyonunu oluşturmaz.
- Public permissions tanımlamaz.
- Frontend'i Directus'a bağlamaz.
- Mevcut statik Academy registry'sini değiştirmez veya silmez.

## D1 schema governance ve local reconstruction

`schema/`, 29 Eylül 2026 tarihinde Production Directus'tan yalnız desteklenen
HTTP `GET` metadata endpoint'leriyle alınan secret-free CURRENT şema ve erişim
snapshot'larını içerir. Makale/content item kayıtları export edilmemiştir.

Local reconstruction production Neon veya R2 kullanmaz. İzole PostgreSQL,
filesystem storage ve `directus/directus:12.2.0` image'ı kullanır:

```powershell
powershell -ExecutionPolicy Bypass -File directus/scripts/reconstruct.ps1
```

Script temiz disposable servisleri açar, pinned image içindeki resmi
`node /directus/cli.js schema apply --yes` komutuyla
`schema/schema.snapshot.json` dosyasını uygular, synthetic draft ve
published kayıtlarla Academy published-only sözleşmesini doğrular ve varsayılan
olarak volume'lerle birlikte ortamı kapatır. İnceleme için ayakta tutmak gerekirse
`-KeepRunning` kullanılabilir.

Şema snapshot'ı collection/field/relation durumunu yeniden kurar. Directus
schema snapshot formatı roller, policy ve permission kayıtlarını uygulamaz;
bunların sanitized CURRENT görünümü `schema/permissions.snapshot.json` içinde
ayrı tutulur. Production `DIRECTUS_SERVICE_TOKEN` kullanıcısının kimliği ve
policy ataması D1'de güvenli biçimde doğrulanamadığından UNKNOWN kalır. CURRENT
backend için admin olmayan published-only TARGET policy sözleşmesi
`access/academy-service-policy.target.json` içindedir ve Production'a
uygulanmamıştır.

### D1.1 closeout

Pinlenmiş image identity'si iki local tag için aynı digest ile doğrulandı. İki
bağımsız boş PostgreSQL volume'ünden reconstruction, resmi schema apply,
synthetic published-only kabulü ve gerçek backend client testi geçti. Her iki
koşu aynı semantic fingerprint'i üretti; kanıt
`schema/reconstruction_evidence.json` içindedir. Runtime-critical schema ve
permission contract yeniden kurulabilir olduğundan DIRECTUS-D1 COMPLETE'tir.
Production service-token assignment doğrulaması D5 security acceptance item'ı
olarak açıkça korunur.

## D2 Academy content contract CURRENT

Backend liste istemcisi artık bounded sayfa boyutu, açık `page`/`limit` ve
`-published_at,sort,id` sırasıyla tüm uygun kayıtları son kısa/boş sayfaya kadar
okur. Tek bir timezone-aware UTC governed time; liste, slug detayı ve bu listeyi
kullanan sitemap için şu kanonik koşulu yönetir:

`status = published AND published_at IS NOT NULL AND published_at <= governed_time`

DTO katmanı timezone bilgisi olmayan timestamp'leri reddeder. Directus filtresine
rağmen uygunsuz kayıt dönerse uygulama ikinci kez fail-closed doğrulama yapar.
Sayfalar arasında tekrar eden `id` veya `slug`, aşırı sayfa ve bozuk tek kayıt
sessizce atlanmaz; tüm liste 502'ye eşlenen gözlemlenebilir payload hatasıyla
başarısız olur. Sitemap aynı servis listesini kullandığı için ayrı bir yayın
evreni veya gizli truncation davranışı yoktur; `lastmod`, `updated_at` varsa onu,
yoksa `published_at` değerini kullanır.

Disposable reconstruction doğrulaması iki kayıtlık sayfa boyutuyla üç uygun
kaydı birden fazla sayfadan okur; draft ve future-published kayıtları dışarıda
tutar; eşit-zaman sınırını liste ve detayda kabul eder. Bu D2 değişiklikleri
Production'a uygulanmamış ve Production verisine erişmemiştir.

### Sonraki faz sınırları

- D3: medya çözümleme, Directus asset/R2 delivery ve bunun minimum file policy'si.
- D4: D4A mimari denetimi ve D4B repository uygulaması tamamlandı; request-time
  metadata shell, crawler/social preview ve gerçek public article HTTP status
  davranışı Production canary/rewrite uygulanana kadar release-pending'dir.
- D5: Production service-token kimliği, TARGET policy assignment ve production
  security acceptance. Bu aşamaya kadar assignment `UNKNOWN` kalır.

## D4B dynamic Academy HTML repository status

D4B'nin backend uygulaması repository içinde **IMPLEMENTED / LOCAL-VERIFIED**
durumdadır. Public `GET|HEAD /api/public/academy/html/{slug}` endpoint'i D2
AcademyService uygunluğunu kullanır, sabit güvenilir Vite shell'ini bounded ve
koşullu cache ile edinir ve parser üzerinden article metadata/JSON-LD ekler.
Frontend React SEO bileşenleri SPA navigation için değişmeden kalır. Ayrıntılı
sözleşme `docs/content/DIRECTUS_D4B_DYNAMIC_HTML.md` içindedir.

Render `/akademi/:slug` rewrite'ı **uygulanmamıştır**. Deploy ve Production
canary yapılmamıştır. P10G-B durumu **PRODUCTION CANARY PENDING** olarak kalır.
