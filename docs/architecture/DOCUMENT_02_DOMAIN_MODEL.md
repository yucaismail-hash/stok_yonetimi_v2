DOCUMENT 02
PART 01 — BUSINESS DOMAIN & CORE CONCEPTS
1. Purpose

Bu doküman, Stokonomi'nin resmi iş alanını (Business Domain) tanımlar.

Bu doküman;

sistemin neyi çözdüğünü,
hangi kavramların resmi olduğunu,
hangi kavramların sistemin merkezinde bulunduğunu,
sonraki tüm mimari kararların hangi domain modeli üzerine kurulacağını

tanımlar.

Bu doküman teknik implementasyon içermez.

Bu doküman yalnızca Business Domain Specification'dır.

2. Business Vision

Stokonomi;

AI destekli karar zekâsı kullanan kurumsal stok optimizasyon platformudur.

Sistem;

yalnızca Forecast üreten,
yalnızca Safety Stock hesaplayan,
yalnızca Simulation yapan

bir yazılım değildir.

Sistemin amacı;

işletmenin stok kararlarını veri odaklı ve açıklanabilir biçimde optimize etmektir.

3. Business Problem

İşletmeler aşağıdaki problemlerin tamamını aynı anda yaşarlar.

Demand Uncertainty

Talep gelecekte kesin olarak bilinemez.

Lead Time Variability

Tedarik süresi değişkendir.

Inventory Cost

Fazla stok maliyet oluşturur.

Stockout Risk

Yetersiz stok satış kaybına neden olur.

Decision Complexity

Bir karar;

Forecast
Safety Stock
Supplier
Seasonality
Pattern
Learning
Risk
Service Level

gibi onlarca faktörün birleşimidir.

Bu nedenle tek bir algoritma doğru karar veremez.

4. Business Philosophy

Stokonomi'nin temel yaklaşımı:

İşletmeler stok yönetmez.

İşletmeler;

belirsizliği,
riski,
maliyeti,
servis seviyesini

dengelemeye çalışırlar.

Dolayısıyla sistemin optimize ettiği şey stok değil,

karar kalitesidir.

5. Core Business Principle

Sistemin merkezinde analizler bulunmaz.

Sistemin merkezinde Business Objective bulunur.

Bir kullanıcı sisteme;

"Forecast çalıştır"

demez.

Şöyle der:

Stok fazlasını azalt.
Servis seviyesini artır.
Nakit bağlamayı azalt.
Kritik ürünleri güvence altına al.
Depo maliyetini düşür.

Bu hedefler sistem tarafından Business Objective olarak yorumlanır.

6. Canonical Business Flow

Stokonomi'nin resmi iş akışı aşağıdaki gibidir.

Business Objective
        │
        ▼
Dataset
        │
        ▼
Workflow
        │
        ▼
Execution
        │
        ▼
Capability Selection
        │
        ▼
Analytical Engines
        │
        ▼
Learning
        │
        ▼
Decision Intelligence
        │
        ▼
AI Artifact

Bu akış, sistemin resmi Business Flow'udur.

Hiçbir modül bu akışı bypass edemez.

7. Core Concepts

Stokonomi aşağıdaki kavramları resmi Domain nesneleri olarak kabul eder.

Concept	Description
Company	Sistemi kullanan işletme
User	İşletme kullanıcısı
Dataset	Analiz için yüklenen veri kümesi
Business Objective	İş hedefi
Workflow	Objective'e göre oluşturulan işlem planı
Execution	Workflow çalıştırması
Capability	Kullanılabilecek analiz yeteneği
Learning	Sistemin kazandığı bilgi
Decision Intelligence	Son karar üretim katmanı
AI Artifact	Kullanıcıya teslim edilen resmi çıktı
Integration	ERP / API / dış sistem bağlantısı
Event	İş alanında meydana gelen değişim

Bu kavramlar Document 02 boyunca detaylandırılacaktır.

8. Domain Scope

Bu doküman aşağıdaki alanları kapsar:

İş hedefleri
Veri yaşam döngüsü
Execution modeli
Öğrenme modeli
AI çıktıları
Domain kuralları
Aggregate sınırları

Bu doküman;

API
Database
UI
Event Bus
Security

detaylarını kapsamaz.

9. Architectural Principle

Business Domain hiçbir teknik implementasyona bağımlı değildir.

Domain;

FastAPI'den bağımsızdır.
PostgreSQL'den bağımsızdır.
Gemini'den bağımsızdır.
React'tan bağımsızdır.
Python'dan bağımsızdır.

Teknolojiler değişebilir.

Business Domain değişmez.

10. Official Principles
Business Objective sistemin başlangıç noktasıdır.
Workflow yalnızca Objective'den üretilir.
Execution yalnızca Workflow çalıştırır.
Capability'ler bağımsız analiz yetenekleridir.
Learning her Execution'dan sonra güncellenir.
Decision Intelligence nihai kararı üretir.
Kullanıcıya yalnızca AI Artifact sunulur.
Domain modeli teknik implementasyondan bağımsızdır.
PART 01 FREEZE CHECKLIST
DOCUMENT 02
PART 01

☑ Business Domain tanımlandı
☑ Business Vision tanımlandı
☑ Business Problem tanımlandı
☑ Business Philosophy tanımlandı
☑ Core Business Principle tanımlandı
☑ Canonical Business Flow tanımlandı
☑ Core Concepts tanımlandı
☑ Domain Scope belirlendi
☑ Architectural Principles tanımlandı
☑ Official Domain Rules belirlendi

STATUS

DOMAIN FOUNDATION FREEZE CANDIDATE

DOCUMENT 02
PART 02 — CORE DOMAIN ENTITIES
1. Purpose

Bu bölüm, Stokonomi'nin resmi Domain Entity modelini tanımlar.

Entity'ler;

sistemin temel iş nesnelerini,
yaşam döngülerini,
birbirleriyle olan ilişkilerini

tanımlar.

Bu bölüm herhangi bir veritabanı modeli değildir.

Bu bölüm tamamen Business Domain seviyesindedir.

2. Canonical Entity Model

Stokonomi aşağıdaki ana Domain Entity'lerini tanımlar.

Company
    │
    ├──────────────┐
    │              │
    ▼              ▼
User          Integration
    │
    ▼
Dataset
    │
    ▼
Business Objective
    │
    ▼
Workflow
    │
    ▼
Execution
    │
    ├──────────────┐
    │              │
    ▼              ▼
Learning      AI Artifact
                    │
                    ▼
Decision Intelligence

Bu yapı sistemin resmi Domain Modelidir.

3. Company

Company, sistemdeki en üst Business Entity'dir.

Her veri

Dataset
Execution
Learning
AI Artifact
Integration

bir Company'ye aittir.

Hiçbir veri şirketler arasında paylaşılmaz.

Responsibilities

Company;

sahiplik (ownership)
izolasyon
yetkilendirme
öğrenme alanı

oluşturur.

4. User

User, Company adına sistemi kullanan aktördür.

User;

Dataset yükler.
Objective oluşturur.
Analiz başlatır.
Sonuçları görüntüler.

User karar üretmez.

Karar üretimi sistem tarafından yapılır.

5. Dataset

Dataset sisteme giren resmi veri kümesidir.

Dataset;

Excel
ERP
API
Integration

üzerinden gelebilir.

Dataset immutable kabul edilir.

Veri değişirse yeni Dataset oluşur.

Dataset Responsibilities

Dataset;

doğrulanabilir
versiyonlanabilir
tekrar kullanılabilir

olmalıdır.

6. Business Objective

Business Objective sistemin başlangıç noktasıdır.

Kullanıcı doğrudan analiz istemez.

Kullanıcı iş hedefi tanımlar.

Örneğin;

Stok fazlasını azalt.
Servis seviyesini artır.
Kritik ürünleri koru.
Nakit bağlamayı azalt.

Business Objective;

hangi analizlerin çalışacağını belirlemez.

Sadece hedefi tanımlar.

7. Workflow

Workflow,

Business Objective'nin yürütülebilir plana dönüşmüş halidir.

Workflow;

hangi Capability'lerin çalışacağını,
çalışma sırasını,
bağımlılıklarını

belirler.

Workflow;

Execution değildir.

Workflow yalnızca plandır.

8. Execution

Execution,

Workflow'un tek çalıştırılmasıdır.

Execution;

başlangıç zamanı,
bitiş zamanı,
durum,
kullanılan Dataset,
kullanılan Workflow,
üretilen çıktılar

ile tanımlanır.

Execution her zaman tekildir.

9. Capability

Capability,

sistemin sahip olduğu analiz yeteneğidir.

Örnek Capability'ler:

Forecast
Safety Stock
Simulation
Supplier
Backtest
Pattern Detection
Seasonality
Classification

Capability'ler bağımsızdır.

Workflow bunlardan uygun olanları seçer.

10. Learning

Learning,

Execution sonrasında sistemin edindiği bilgidir.

Learning;

Company Learning
Pattern Learning
Decision Learning

katmanlarından oluşur.

Learning doğrudan kullanıcı tarafından yönetilemez.

11. Decision Intelligence

Decision Intelligence,

tüm analizleri birleştirerek

tek bir karar üretir.

Bu katman;

Forecast
Safety Stock
Supplier
Learning
Risk
Pattern

çıktılarını birlikte değerlendirir.

Karar üreten tek resmi bileşendir.

12. AI Artifact

AI Artifact,

Execution sonucunun kullanıcıya sunulan resmi temsilidir.

AI Artifact;

rapor
dashboard
explainability
öneriler
risk değerlendirmesi

gibi tüm çıktıların tek kapsayıcısıdır.

Kullanıcı hiçbir zaman ham analiz sonucu tüketmez.

Daima AI Artifact tüketir.

13. Integration

Integration,

Stokonomi ile dış sistemler arasındaki resmi bağlantıdır.

Örnek:

ERP
SAP
Logo
Mikro
Nebim
REST API
Webhook

Integration iş mantığı içermez.

Sadece veri taşır.

14. Event

Event,

Business Domain içerisinde gerçekleşen değişmez (immutable) iş olayıdır.

Örnek:

DatasetUploaded
WorkflowCreated
ExecutionStarted
ExecutionCompleted
LearningUpdated
ArtifactPublished

Event geçmişi temsil eder.

Hiçbir zaman değiştirilemez.

15. Entity Relationship Summary
Company
    │
    ├── Users
    ├── Datasets
    ├── Executions
    ├── Learning
    ├── AI Artifacts
    └── Integrations

Dataset
    │
    ▼
Business Objective
    │
    ▼
Workflow
    │
    ▼
Execution
    │
    ├── Learning
    └── AI Artifact
16. Official Entity Rules
Company tüm varlıkların sahibidir.
User yalnızca işlemi başlatır.
Dataset immutable'dır.
Business Objective iş hedefini tanımlar.
Workflow yalnızca yürütme planıdır.
Execution tek bir çalıştırmadır.
Capability bağımsız analiz yeteneğidir.
Learning yalnızca Execution sonrasında güncellenir.
Decision Intelligence tek resmi karar üreticisidir.
AI Artifact kullanıcıya sunulan tek resmi çıktıdır.
Integration yalnızca veri alışverişi yapar.
Event değiştirilemez iş olayıdır.
PART 02 FREEZE CHECKLIST
DOCUMENT 02
PART 02

☑ Canonical Entity Model tanımlandı
☑ Company tanımlandı
☑ User tanımlandı
☑ Dataset tanımlandı
☑ Business Objective tanımlandı
☑ Workflow tanımlandı
☑ Execution tanımlandı
☑ Capability tanımlandı
☑ Learning tanımlandı
☑ Decision Intelligence tanımlandı
☑ AI Artifact tanımlandı
☑ Integration tanımlandı
☑ Event tanımlandı
☑ Entity Relationships oluşturuldu
☑ Official Entity Rules tanımlandı

STATUS

ENTITY MODEL FREEZE CANDIDATE

DOCUMENT 02
PART 03 — DOMAIN RELATIONSHIPS & LIFECYCLE
1. Purpose

Bu bölüm;

Domain Entity'lerinin

birbirleriyle olan ilişkilerini,
yaşam döngülerini,
sahiplik kurallarını

tanımlar.

Bu bölüm veri tabanı ilişkisi değildir.

Business Domain ilişkilerini tanımlar.

2. Domain Ownership

Stokonomi'de tüm iş nesneleri bir sahiplik zinciri içerisinde bulunur.

Resmi sahiplik modeli aşağıdaki gibidir.

Company
│
├── Users
├── Datasets
├── Integrations
├── Learnings
├── Executions
├── AI Artifacts
└── Events

Company en üst sahiplik katmanıdır.

Hiçbir Entity Company dışında yaşayamaz.

3. Business Flow Relationship

Entity'ler aşağıdaki sırayla oluşur.

Dataset
      │
      ▼
Business Objective
      │
      ▼
Workflow
      │
      ▼
Execution
      │
      ├────────────┐
      │            │
      ▼            ▼
Learning      AI Artifact
                    │
                    ▼
Decision Intelligence

Bu sıralama sistemin resmi Business Flow'udur.

4. Dataset Lifecycle

Dataset yaşam döngüsü:

Created
    │
Validated
    │
Approved
    │
Active
    │
Archived

Kurallar:

Dataset silinmez.
Dataset değiştirilmez.
Dataset versiyonlanır.
Active Dataset şirket başına tektir.
5. Business Objective Lifecycle

Business Objective;

Created
    │
Accepted
    │
Planned
    │
Completed

Business Objective doğrudan çalıştırılmaz.

Önce Workflow oluşturulur.

6. Workflow Lifecycle

Workflow;

Generated
      │
Validated
      │
Ready
      │
Executed
      │
Closed

Workflow tekrar kullanılabilir.

Workflow immutable kabul edilir.

7. Execution Lifecycle

Execution sistemin en önemli Entity'lerinden biridir.

Yaşam döngüsü:

Created
     │
Queued
     │
Running
     │
Completed
     │
Published

Alternatif durumlar:

Running
    │
Failed

Running
    │
Cancelled

Running
    │
Timed Out

Execution geçmişi değiştirilemez.

8. Learning Lifecycle

Learning;

Waiting
    │
Collecting
    │
Analyzing
    │
Updated

Learning hiçbir zaman kullanıcı isteğiyle güncellenmez.

Sadece başarılı Execution sonrasında güncellenebilir.

9. AI Artifact Lifecycle

AI Artifact;

Generated
      │
Validated
      │
Published
      │
Versioned
      │
Archived

Kullanıcı yalnızca Published Artifact görebilir.

10. Integration Lifecycle

Integration;

Configured
      │
Verified
      │
Active
      │
Suspended
      │
Disabled

Integration başarısız olsa bile sistem çalışmaya devam eder.

11. Event Lifecycle

Event;

Created
     │
Persisted
     │
Published
     │
Delivered
     │
Archived

Event değiştirilemez.

Replay işlemleri yeni Event üretmez.

Mevcut Event yeniden yayınlanır.

12. Relationship Rules
Company

Company;

birçok User'a sahiptir.
birçok Dataset'e sahiptir.
birçok Execution'a sahiptir.
birçok Learning kaydına sahiptir.
birçok AI Artifact'e sahiptir.
birçok Integration'a sahiptir.
Dataset

Dataset;

tek Company'ye aittir.
birçok Execution tarafından kullanılabilir.
birçok Workflow tarafından referans alınabilir.
Workflow

Workflow;

tek Business Objective'den oluşur.
birçok Execution üretebilir.
Execution

Execution;

tek Workflow çalıştırır.
tek Dataset kullanır.
tek AI Artifact üretir.
Learning'i günceller.
Event üretir.
AI Artifact

AI Artifact;

tek Execution'a aittir.
kullanıcıya sunulan tek resmi çıktıdır.
Learning

Learning;

Company seviyesinde saklanır.
birçok Execution'dan beslenebilir.
13. Aggregate Boundaries

Domain Aggregate sınırları aşağıdaki gibidir.

Company Aggregate
│
├── Users
├── Integrations
├── Learnings
└── Policies

Execution Aggregate
│
├── Workflow
├── Dataset
├── AI Artifact
└── Events

Aggregate sınırları Transaction Boundary olarak kabul edilir.

14. Identity Rules

Her Entity benzersiz kimliğe sahiptir.

Company
UUID

User
UUID

Dataset
UUID

Workflow
UUID

Execution
UUID

AI Artifact
UUID

Integration
UUID

Event
UUID

Kimlikler hiçbir zaman yeniden kullanılmaz.

15. Consistency Rules

Sistem aşağıdaki tutarlılık kurallarını garanti eder.

Execution yalnızca Approved Dataset kullanabilir.
Workflow yalnızca geçerli Business Objective'den üretilebilir.
Learning yalnızca başarılı Execution sonrasında güncellenebilir.
AI Artifact yalnızca Completed Execution'dan üretilebilir.
Event yalnızca gerçekleşmiş Business Fact'i temsil eder.
Company izolasyonu hiçbir zaman ihlal edilemez.
16. Official Lifecycle Rules
Entity yaşam döngüleri geri alınamaz.
Entity geçmişi korunur.
Immutable Entity'ler güncellenmez.
Version oluşturularak değişiklik yapılır.
Aggregate sınırları ihlal edilmez.
Company tüm Entity'lerin sahibidir.
Execution sistemin temel çalışma birimidir.
AI Artifact kullanıcıya sunulan tek resmi çıktıdır.
PART 03 FREEZE CHECKLIST
DOCUMENT 02
PART 03

☑ Domain Ownership tanımlandı
☑ Business Flow tanımlandı
☑ Dataset Lifecycle tanımlandı
☑ Business Objective Lifecycle tanımlandı
☑ Workflow Lifecycle tanımlandı
☑ Execution Lifecycle tanımlandı
☑ Learning Lifecycle tanımlandı
☑ AI Artifact Lifecycle tanımlandı
☑ Integration Lifecycle tanımlandı
☑ Event Lifecycle tanımlandı
☑ Relationship Rules tanımlandı
☑ Aggregate Boundaries tanımlandı
☑ Identity Rules tanımlandı
☑ Consistency Rules tanımlandı
☑ Official Lifecycle Rules tanımlandı

STATUS

DOMAIN RELATIONSHIPS FREEZE CANDIDATE

DOCUMENT 02
PART 04 — CAPABILITY MODEL
1. Purpose

Bu bölüm, Stokonomi'nin sahip olduğu resmi iş yeteneklerini (Capabilities) tanımlar.

Capability;

bir analiz modülü,
bir servis,
bir API

değildir.

Capability, sistemin yerine getirebildiği iş fonksiyonudur.

Workflow'lar bu Capability'leri kullanarak Business Objective'leri gerçekleştirir.

2. Capability Definition

Capability;

belirli bir iş problemini çözebilen bağımsız sistem davranışıdır.

Bir Capability;

giriş alır,
analiz yapar,
çıktı üretir,
diğer Capability'lerden bağımsız çalışabilir.

Capability hiçbir zaman Entity değildir.

3. Official Capability Model

Stokonomi aşağıdaki resmi Capability setini tanımlar.

Business Objective
        │
        ▼
Workflow
        │
        ▼
Capability Registry
        │
 ┌──────┼────────┬────────┬────────┬────────┬────────┐
 ▼      ▼        ▼        ▼        ▼        ▼
Forecast Safety  Supplier Simulation Backtest Learning
         Stock
        │
        └──────────────┐
                       ▼
              Decision Intelligence

Decision Intelligence analiz yapan bir Capability değildir.

Karar üreten üst katmandır.

4. Forecast Capability

Forecast Capability;

gelecek talebi tahmin eder.

Sorumlulukları;

talep tahmini
trend analizi
sezon analizi
tahmin güveni
forecast explainability

Ürettiği çıktı;

Forecast Result'dır.

5. Safety Stock Capability

Safety Stock Capability;

stok riskini hesaplar.

Sorumlulukları;

emniyet stoğu
servis seviyesi
stok riski
yeniden sipariş noktası
stok tamponu

Ürettiği çıktı;

Safety Stock Result'dır.

6. Simulation Capability

Simulation Capability;

farklı senaryoları test eder.

Sorumlulukları;

Monte Carlo
senaryo üretimi
risk dağılımı
servis seviyesi simülasyonu
maliyet analizi

Ürettiği çıktı;

Simulation Result'dır.

7. Supplier Capability

Supplier Capability;

tedarik performansını analiz eder.

Sorumlulukları;

Lead Time
Supplier Risk
Supplier Reliability
Tedarikçi Performansı
Teslimat Analizi

Ürettiği çıktı;

Supplier Result'dır.

8. Backtest Capability

Backtest Capability;

analiz kalitesini geçmiş veri üzerinde doğrular.

Sorumlulukları;

Forecast Accuracy
Method Comparison
Historical Validation
Error Analysis
Confidence Measurement

Ürettiği çıktı;

Backtest Result'dır.

9. Learning Capability

Learning Capability;

Execution sonrasında bilgi üretir.

Alt katmanları;

Company Learning
Pattern Learning
Decision Learning

Learning hiçbir zaman doğrudan kullanıcı tarafından çalıştırılmaz.

10. Decision Intelligence

Decision Intelligence;

Capability değildir.

Decision Intelligence;

tüm Capability çıktılarını değerlendirerek

tek bir karar üretir.

Kullandığı girdiler;

Forecast
Safety Stock
Simulation
Supplier
Backtest
Learning

Ürettiği çıktı;

AI Decision'dır.

11. Capability Independence

Her Capability;

bağımsız geliştirilebilir,
bağımsız test edilebilir,
bağımsız versiyonlanabilir.

Hiçbir Capability başka bir Capability'nin iç mantığını bilemez.

İletişim yalnızca resmi veri modelleri üzerinden yapılır.

12. Capability Dependencies

Capability'ler arasında zorunlu bağımlılık bulunmaz.

Workflow gerekli olduğunda bağımlılık oluşturur.

Örnek:

Forecast
     │
     ▼
Safety Stock

veya

Forecast

Simulation

Supplier

↓

Decision Intelligence

Bağımlılık Workflow tarafından belirlenir.

Capability tarafından değil.

13. Capability Inputs

Her Capability yalnızca resmi girdileri kullanır.

Örnek girdiler;

Dataset
Workflow Parameters
Execution Context
Company Context
Learning Context

Capability doğrudan veritabanı sorgusu yapmaz.

14. Capability Outputs

Her Capability tek tip çıktı üretir.

Forecast
      ▼
Forecast Result

Safety Stock
      ▼
Safety Stock Result

Simulation
      ▼
Simulation Result

Supplier
      ▼
Supplier Result

Backtest
      ▼
Backtest Result

Learning
      ▼
Learning Result

Karışık veri modelleri kullanılmaz.

15. Capability Rules
Capability iş yeteneğidir.
Capability Entity değildir.
Capability bağımsızdır.
Capability yalnızca resmi girdileri kullanır.
Capability yalnızca resmi çıktı üretir.
Capability başka Capability'nin iç mantığını çağırmaz.
Workflow Capability seçiminden sorumludur.
Decision Intelligence tek karar üreticisidir.
16. Capability Registry

Workflow Engine;

Capability'leri doğrudan oluşturmaz.

Capability Registry üzerinden erişir.

Workflow
      │
      ▼
Capability Registry
      │
 ┌────┼────┬────┬────┬────┐
 ▼    ▼    ▼    ▼    ▼
Forecast
Safety Stock
Simulation
Supplier
Backtest
Learning

Bu yapı;

yeni Capability eklenmesini,
Capability değiştirilmesini,
Capability versiyonlanmasını

kolaylaştırır.

PART 04 FREEZE CHECKLIST
DOCUMENT 02
PART 04

☑ Capability tanımı yapıldı
☑ Capability Model oluşturuldu
☑ Forecast Capability tanımlandı
☑ Safety Stock Capability tanımlandı
☑ Simulation Capability tanımlandı
☑ Supplier Capability tanımlandı
☑ Backtest Capability tanımlandı
☑ Learning Capability tanımlandı
☑ Decision Intelligence tanımlandı
☑ Capability Independence tanımlandı
☑ Capability Dependencies tanımlandı
☑ Capability Inputs tanımlandı
☑ Capability Outputs tanımlandı
☑ Capability Rules tanımlandı
☑ Capability Registry tanımlandı

STATUS

CAPABILITY MODEL FREEZE CANDIDATE

DOCUMENT 02
PART 05 — OBJECTIVE TO CAPABILITY MAPPING
1. Purpose

Bu bölüm;

Business Objective'lerin

Capability'lere nasıl dönüştürüldüğünü tanımlar.

Business Objective hiçbir zaman doğrudan bir analiz çalıştırmaz.

Önce Workflow oluşturulur.

Workflow gerekli Capability'leri belirler.

2. Mapping Principle

Business Objective;

iş hedefidir.

Capability;

işi gerçekleştiren yetenektir.

İkisi aynı kavram değildir.

Business Objective
        │
        ▼
Workflow Planner
        │
        ▼
Capability Selection
        │
        ▼
Execution
3. Official Mapping Flow

Stokonomi aşağıdaki resmi dönüşümü kullanır.

User Request
      │
      ▼
Business Objective
      │
      ▼
Objective Planner
      │
      ▼
Workflow
      │
      ▼
Capability Registry
      │
      ▼
Execution

API hiçbir zaman Capability seçmez.

4. Objective Examples

Örnek:

Amaç
Stok maliyetini azalt.

Planner aşağıdaki Capability'leri seçebilir.

Forecast

Safety Stock

Simulation

Decision Intelligence

Başka bir örnek

Tedarik riskini azalt.

Planner

Supplier

Forecast

Simulation

Decision Intelligence

çalıştırabilir.

5. Objective Planner

Objective Planner;

Business Objective'yi yorumlayan bileşendir.

Görevleri;

Objective analizi
Capability seçimi
Dependency çözümü
Workflow oluşturma

Planner analiz çalıştırmaz.

6. Capability Selection

Capability seçimi;

Objective
Dataset özellikleri
Company Policy
Kullanılabilir Capability'ler

üzerinden yapılır.

Örnek;

Objective

↓

Forecast

↓

Safety Stock

↓

Simulation

veya

Objective

↓

Forecast

↓

Decision Intelligence
7. Mandatory Capabilities

Bazı Objective'ler zorunlu Capability gerektirir.

Örneğin;

Demand Optimization

için

Forecast

zorunludur.

Safety Stock ise isteğe bağlı olabilir.

8. Optional Capabilities

Workflow;

opsiyonel Capability'leri de çalıştırabilir.

Örneğin;

Forecast

Safety Stock

Supplier

Simulation

Simulation başarısız olsa bile

Forecast sonucu kullanılabilir.

9. Dependency Resolution

Dependency;

Workflow tarafından çözülür.

Capability'ler dependency çözmez.

Örnek

Forecast
     │
     ▼
Safety Stock

Forecast tamamlanmadan

Safety Stock çalıştırılmaz.

10. Capability Ordering

Workflow;

Capability çalışma sırasını belirler.

Örnek

Forecast

↓

Pattern Detection

↓

Safety Stock

↓

Simulation

↓

Decision Intelligence

Bu sıra Objective'ye göre değişebilir.

11. Parallel Execution

Bağımsız Capability'ler

aynı anda çalıştırılabilir.

Forecast

Supplier

Backtest

Paralel çalışma mümkündür.

Workflow bunu yönetir.

12. Fallback Strategy

Bir Capability başarısız olduğunda

Workflow alternatif yolları deneyebilir.

Örnek

Forecast

↓

FAILED

↓

Fallback Forecast

↓

Safety Stock

Sistem mümkün olduğunca Objective'yi tamamlamaya çalışır.

13. Graceful Degradation

Workflow;

opsiyonel Capability başarısız olsa bile

çalışmaya devam edebilir.

Örnek

Forecast

↓

Supplier FAILED

↓

Decision Intelligence

Decision Intelligence mevcut verilerle karar üretir.

14. Objective Completion

Business Objective;

tek bir analiz tamamlanınca bitmez.

Objective;

Workflow başarıyla tamamlandığında tamamlanmış kabul edilir.

15. Mapping Rules
Objective analiz değildir.
Objective Capability değildir.
Planner yalnızca Workflow üretir.
Workflow Capability seçer.
Capability bağımsız çalışır.
Dependency yalnızca Workflow tarafından çözülür.
Parallel Execution desteklenir.
Fallback mekanizması Workflow tarafından yönetilir.
Graceful Degradation resmi davranıştır.
Decision Intelligence son adımdır.
16. Official Mapping Architecture
Business Objective
        │
        ▼
Objective Planner
        │
        ▼
Workflow
        │
        ▼
Capability Registry
        │
        ▼
Execution Engine
        │
        ▼
Capability Results
        │
        ▼
Decision Intelligence
        │
        ▼
AI Artifact

Bu mimari,

Document 07'de tanımlanan Workflow Dispatcher, Execution Engine ve Capability Registry mimarisiyle birebir uyumludur.

PART 05 FREEZE CHECKLIST
DOCUMENT 02
PART 05

☑ Objective tanımlandı
☑ Objective Planner tanımlandı
☑ Capability Mapping tanımlandı
☑ Capability Selection tanımlandı
☑ Mandatory Capability kuralları tanımlandı
☑ Optional Capability kuralları tanımlandı
☑ Dependency Resolution tanımlandı
☑ Capability Ordering tanımlandı
☑ Parallel Execution tanımlandı
☑ Fallback Strategy tanımlandı
☑ Graceful Degradation tanımlandı
☑ Objective Completion tanımlandı
☑ Mapping Rules tanımlandı
☑ Official Mapping Architecture oluşturuldu

STATUS

OBJECTIVE MAPPING FREEZE CANDIDATE

DOCUMENT 02
PART 06 — DOMAIN RULES & BUSINESS CONSTRAINTS
1. Purpose

Bu bölüm;

Stokonomi Domain'inin değiştirilemez iş kurallarını (Business Constraints) tanımlar.

Bu kurallar;

Workflow
Execution
Learning
Decision Intelligence
AI Artifact
Integration

tarafından her zaman uygulanmalıdır.

Hiçbir modül bu kuralları ihlal edemez.

2. Business Invariants

Business Invariant;

sistemin her durumda doğru kalmasını sağlayan resmi kuraldır.

Invariant;

konfigürasyon değildir.
öneri değildir.
zorunludur.
3. Company Isolation

Her veri yalnızca ait olduğu Company içerisinde kullanılabilir.

Hiçbir durumda;

Dataset
Execution
Learning
AI Artifact
Event

başka bir Company tarafından görülemez.

4. Dataset Rules

Dataset için resmi kurallar:

Dataset immutable'dır.
Dataset silinmez.
Dataset güncellenmez.
Yeni veri yeni Dataset oluşturur.
Approved olmayan Dataset çalıştırılamaz.
Aynı anda yalnızca bir Active Dataset bulunabilir.
5. Workflow Rules

Workflow;

yalnızca Business Objective'den üretilir.
manuel oluşturulamaz.
Execution sırasında değiştirilemez.
oluşturulduktan sonra immutable kabul edilir.

Workflow iş mantığı içermez.

Yalnızca yürütme planıdır.

6. Execution Rules

Execution;

tek Workflow çalıştırır.
tek Dataset kullanır.
tek Company'ye aittir.
tamamlandıktan sonra değiştirilemez.
geçmişi korunur.

Execution tekrar kullanılmaz.

Her çalıştırma yeni Execution oluşturur.

7. Capability Rules

Capability;

bağımsız çalışmalıdır.
başka Capability'nin iç mantığını bilemez.
yalnızca resmi girdileri kullanabilir.
yalnızca resmi çıktı üretebilir.

Capability seçiminden Workflow sorumludur.

8. Learning Rules

Learning;

yalnızca başarılı Execution sonrasında güncellenebilir.
kullanıcı tarafından değiştirilemez.
geçmiş Learning kayıtlarını bozmaz.
Company seviyesinde saklanır.

Learning başarısız olsa bile Execution geçerliliğini korur.

9. Decision Intelligence Rules

Decision Intelligence;

tek resmi karar üreticisidir.
ham analiz sonucu yayımlamaz.
tüm Capability sonuçlarını birlikte değerlendirir.
eksik veri olduğunda mevcut bilgilerle karar üretmeye çalışır.

Decision Intelligence doğrudan Capability çalıştırmaz.

10. AI Artifact Rules

AI Artifact;

yalnızca Completed Execution'dan üretilebilir.
kullanıcıya sunulan tek resmi çıktıdır.
immutable kabul edilir.
versiyonlanabilir.
Explainability içermelidir.

Ham Execution Result kullanıcıya gösterilmez.

11. Event Rules

Event;

gerçekleşmiş bir Business Fact'i temsil eder.
immutable'dır.
tekrar yazılmaz.
silinmez.
replay edilebilir.
versiyonlanabilir.

Event iş mantığı çalıştırmaz.

12. Integration Rules

Integration;

yalnızca veri taşır.
iş kararı üretmez.
Event üretmez.
Capability çalıştırmaz.
Workflow oluşturmaz.

Integration başarısız olsa bile sistem çalışmaya devam eder.

13. Failure Rules

Sistem aşağıdaki durumlarda tamamen durmamalıdır.

Forecast başarısız olabilir.
Supplier başarısız olabilir.
Learning başarısız olabilir.
Integration başarısız olabilir.

Workflow mümkün olan en iyi sonucu üretmeye devam eder.

Bu davranış Graceful Degradation olarak kabul edilir.

14. Dependency Rules

Hiçbir katman aşağıdaki sınırları ihlal edemez.

API

↓

Application

↓

Workflow

↓

Execution Engine

↓

Capability

↓

Learning

↓

Decision Intelligence

↓

AI Artifact

Alt katman üst katmanı çağıramaz.

Bağımlılık tek yönlüdür.

15. Versioning Rules

Versiyonlanan nesneler:

Dataset
Workflow
AI Artifact
Event

Version oluşturulduktan sonra eski Version değiştirilemez.

16. Security Rules

Her işlem için aşağıdaki bilgiler zorunludur.

Company Identity
User Identity
Execution Identity
Trace Identity

Hiçbir işlem anonim yürütülemez.

17. Audit Rules

Sistem aşağıdaki olayları kaydetmelidir.

Dataset oluşturulması
Workflow oluşturulması
Execution başlangıcı
Execution bitişi
Learning güncellemesi
AI Artifact üretimi
Integration senkronizasyonu

Audit geçmişi silinmez.

18. Official Business Constraints
Company izolasyonu zorunludur.
Dataset immutable'dır.
Workflow immutable'dır.
Execution tek kullanımlıktır.
Capability bağımsızdır.
Learning yalnızca başarılı Execution sonrasında güncellenebilir.
Decision Intelligence tek karar üreticisidir.
AI Artifact kullanıcıya sunulan tek resmi çıktıdır.
Event immutable'dır.
Integration yalnızca veri taşır.
Graceful Degradation resmi davranıştır.
Katman bağımlılıkları tek yönlüdür.
Audit geçmişi korunur.
PART 06 FREEZE CHECKLIST
DOCUMENT 02
PART 06

☑ Business Invariants tanımlandı
☑ Company Isolation kuralları tanımlandı
☑ Dataset Rules tanımlandı
☑ Workflow Rules tanımlandı
☑ Execution Rules tanımlandı
☑ Capability Rules tanımlandı
☑ Learning Rules tanımlandı
☑ Decision Intelligence Rules tanımlandı
☑ AI Artifact Rules tanımlandı
☑ Event Rules tanımlandı
☑ Integration Rules tanımlandı
☑ Failure Rules tanımlandı
☑ Dependency Rules tanımlandı
☑ Versioning Rules tanımlandı
☑ Security Rules tanımlandı
☑ Audit Rules tanımlandı
☑ Official Business Constraints oluşturuldu

STATUS

DOMAIN RULES FREEZE CANDIDATE

DOCUMENT 02
PART 07 — OFFICIAL DOMAIN PRINCIPLES
1. Purpose

Bu bölüm;

Stokonomi Domain'inin resmi mimari prensiplerini tanımlar.

Bu prensipler;

tüm modüller,
tüm servisler,
tüm API'ler,
tüm Workflow'lar

için bağlayıcıdır.

Hiçbir geliştirme bu prensiplere aykırı olamaz.

2. Domain First Principle

Stokonomi teknik katmanlardan önce iş alanını (Domain) tanımlar.

Kod;

Domain'i takip eder.

Domain hiçbir zaman kodu takip etmez.

3. Business Before Technology

İş kuralları;

teknoloji seçimlerinden bağımsızdır.

Python değişebilir.
FastAPI değişebilir.
PostgreSQL değişebilir.

Fakat;

Dataset
Workflow
Execution
Learning
Decision Intelligence

değişmez Domain kavramlarıdır.

4. Objective Driven Architecture

Sistem analiz odaklı değildir.

Sistem;

Business Objective odaklıdır.

Hiçbir kullanıcı

"Forecast çalıştır"

demez.

Kullanıcı;

"Hizmet seviyesini artır."

der.

Sistem gerekli analizleri kendisi seçer.

5. Workflow Driven Execution

Execution;

Capability seçmez.

Workflow;

Execution'ı yönetir.

Workflow;

Capability seçer.
sıralar.
bağımlılıkları çözer.
paralelliği yönetir.
fallback stratejisini uygular.
6. Capability Independence

Her Capability;

bağımsızdır.
test edilebilir.
değiştirilebilir.
versiyonlanabilir.

Hiçbir Capability;

başka bir Capability'nin iç mantığını bilemez.

7. Decision Centric System

Forecast;

karar üretmez.

Safety Stock;

karar üretmez.

Simulation;

karar üretmez.

Supplier;

karar üretmez.

Kararı yalnızca

Decision Intelligence üretir.

8. Progressive Intelligence

Sistem;

her zaman mümkün olan en iyi sonucu üretmeye çalışır.

Bazı Capability'ler çalışmasa bile

mevcut bilgilerle analiz devam eder.

Bu yaklaşım;

Graceful Degradation prensibidir.

9. Learning Never Stops

Her başarılı Execution;

Company Learning'i geliştirir.

Learning;

manuel olarak yönetilmez.

Sistem zamanla daha doğru kararlar üretir.

10. Explainability First

Her karar açıklanabilir olmalıdır.

AI Artifact;

yalnızca sonuç üretmez.

Aynı zamanda;

neden,
nasıl,
hangi verilere göre

karar verildiğini de açıklar.

11. Immutable History

Aşağıdaki nesneler geçmişi temsil eder.

Dataset
Workflow
Execution
Event
AI Artifact

Geçmiş değiştirilemez.

Yeni durum yeni Version oluşturur.

12. Company Isolation

Her Company;

kendi öğrenmesine,

kendi Dataset'lerine,

kendi Decision Intelligence geçmişine sahiptir.

Şirketler arasında bilgi paylaşılmaz.

13. AI Artifact First

Kullanıcı;

ham analiz görmez.

Kullanıcı;

AI Artifact görür.

AI Artifact;

Stokonomi'nin resmi çıktısıdır.

14. Layer Independence

Her katman;

yalnızca kendisinden sonraki katmanı bilir.

API

↓

Application

↓

Workflow

↓

Execution Engine

↓

Capability

↓

Learning

↓

Decision Intelligence

↓

AI Artifact

Katmanlar ters yönde bağımlılık oluşturamaz.

15. Official Domain Principles

Stokonomi aşağıdaki resmi prensiplere bağlıdır.

Domain First
Business Before Technology
Objective Driven
Workflow Driven
Capability Independence
Progressive Intelligence
Explainability First
Company Isolation
Immutable History
AI Artifact First
Layer Independence
16. Architecture Manifest
User

↓

Business Objective

↓

Workflow

↓

Capability Registry

↓

Execution Engine

↓

Capabilities

↓

Learning

↓

Decision Intelligence

↓

AI Artifact

↓

Business Value

Bu akış Stokonomi'nin resmi çalışma modelidir.

17. Official Domain Statement

Stokonomi;

bir analiz platformu değildir.

Stokonomi;

iş hedeflerini,

veriyi,

öğrenmeyi,

karar zekâsını

bir araya getirerek

kurumsal karar üreten

AI destekli bir Decision Intelligence Platformudur.

PART 07 FREEZE CHECKLIST
DOCUMENT 02
PART 07

☑ Domain First tanımlandı
☑ Business Before Technology tanımlandı
☑ Objective Driven Architecture tanımlandı
☑ Workflow Driven Execution tanımlandı
☑ Capability Independence tanımlandı
☑ Decision Centric yaklaşımı tanımlandı
☑ Progressive Intelligence tanımlandı
☑ Learning Never Stops tanımlandı
☑ Explainability First tanımlandı
☑ Immutable History tanımlandı
☑ Company Isolation tanımlandı
☑ AI Artifact First tanımlandı
☑ Layer Independence tanımlandı
☑ Official Domain Principles oluşturuldu
☑ Architecture Manifest oluşturuldu
☑ Official Domain Statement oluşturuldu

STATUS

DOCUMENT 02 FREEZE CANDIDATE

# Revision — Product Architecture Phase 1

- **Revision date:** 2026-08-06
- **Revision status:** BINDING
- **ADR reference:** ADR-020

Binding domain model:

```text
ExecutionIntent
├── SingleAnalysisIntent
└── BusinessObjectiveIntent

Workflow
├── SingleAnalysisWorkflow
└── BusinessObjectiveWorkflow
```

Exactly one intent domain is present: `objective_type XOR analysis_type`. Capability and Business Objective are separate domain concepts and must not be silently mapped to one another. A SingleAnalysisWorkflow contains exactly one selected analytical capability. A BusinessObjectiveWorkflow contains its approved ordered capability chain. Dynamic Operational Plan is a first-class Business Workflow output concept.

Canonical workflow matrix:

- Standalone Forecast: Validation → Forecast → Learning → AI Explanation Artifact.
- Standalone Safety Stock: Validation → Safety Stock → Learning → AI Explanation Artifact.
- Standalone Simulation: Validation → Simulation → Learning → AI Explanation Artifact.
- Standalone Backtest: Validation → Backtest → Learning → AI Explanation Artifact.
- Standalone Supplier: Validation → Supplier → Learning → AI Explanation Artifact.
- Forecast Business Workflow: Validation → Forecast → Simulation → Backtest → Learning → Decision Intelligence → Dynamic Demand Plan → AI Artifact.
- Safety Stock Business Workflow: Validation → Forecast → Safety Stock → Simulation → Backtest → Learning → Decision Intelligence → Dynamic Inventory Plan → AI Artifact.

Supplier data, when available, enriches the Dynamic Inventory Plan through Supplier Allocation. Supplier-data absence does not block the core Dynamic Inventory Plan.

