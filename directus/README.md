# Stokonomi Directus deployment

Bu klasör yalnız Stokonomi içerik platformunun deployment tanımını içerir. Directus;
Akademi, içerik, medya ve SEO için kullanılacaktır. Ana operasyon veritabanına veya
operasyon servislerine bağlanmamalıdır.

## Sabitlenen image

`Dockerfile`, resmi `directus/directus:12.1.1` image'ını kullanır. `latest`, major
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
9. Render HTTP health check path değerini `/server/health` olarak ayarlayın.
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
