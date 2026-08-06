# STOKONOMI ARCHITECTURE SPECIFICATION v2.0

# DOCUMENT 03

# WORKFLOW & EXECUTION ARCHITECTURE

Version: 2.0

Status: Draft → Architecture Freeze Candidate

Priority: Mandatory

Scope: Workflow Lifecycle, Execution Coordination, Capability Orchestration

---

# PART 01 — WORKFLOW FOUNDATION

## 1. PURPOSE

Bu doküman, Stokonomi platformunda iş akışlarının (Workflow) nasıl oluşturulduğunu, yönetildiğini ve yürütüldüğünü tanımlar.

Workflow Architecture;

- Business Objective'nin nasıl çalıştırıldığını,
- Capability seçim sürecini,
- Execution koordinasyonunu,
- AI analizlerinin çalışma sırasını,
- Workflow yaşam döngüsünü

standart hale getirir.

Bu dokümanda tanımlanan kurallar Workflow Engine için bağlayıcıdır.

---

## 2. WORKFLOW DEFINITION

Workflow;

bir Business Objective'nin gerçekleştirilmesi için gerekli tüm analizlerin belirlenen kurallar doğrultusunda yürütülmesini sağlayan resmi süreçtir.

Workflow;

- tek bir analiz değildir,
- tek bir modül değildir,
- yalnızca görev listesi değildir.

Workflow;

Business Objective'nin sistem tarafından uygulanabilir hale dönüştürülmüş yürütme planıdır.

---

## 3. OFFICIAL WORKFLOW OBJECTIVE

Workflow'un amacı;

Business Objective'yi,

doğru Capability'lere,

doğru sırayla,

doğru bağımlılıklarla,

tekrarlanabilir şekilde çalıştırmaktır.

Workflow hiçbir zaman iş kararı üretmez.

Karar üretimi yalnızca Decision Intelligence katmanına aittir.

---

## 4. WORKFLOW RESPONSIBILITIES

Workflow aşağıdaki sorumluluklara sahiptir.

- Business Objective'yi yorumlamak
- Capability seçimini koordine etmek
- Execution sırasını oluşturmak
- Bağımlılıkları yönetmek
- Execution Context oluşturmak
- Workflow Engine'e yürütme planını aktarmak

Workflow aşağıdaki görevleri üstlenemez.

- Forecast hesaplamak
- Safety Stock hesaplamak
- AI yorumu üretmek
- Repository erişimi yapmak
- HTTP isteği yönetmek

---

## 5. WORKFLOW LIFECYCLE

Platformdaki her Workflow aşağıdaki yaşam döngüsünü takip eder.

```
Created
    │
    ▼
Validated
    │
    ▼
Planned
    │
    ▼
Dispatched
    │
    ▼
Executing
    │
    ▼
Completed
```

Başarısız Workflow aşağıdaki duruma geçebilir.

```
Executing
      │
      ▼
Failed
```

İptal edilen Workflow ise aşağıdaki duruma geçer.

```
Executing
      │
      ▼
Cancelled
```

Hiçbir Workflow Completed durumundan tekrar Executing durumuna dönemez.

---

## 6. WORKFLOW TYPES

Platform aşağıdaki Workflow türlerini destekler.

### Business Objective Workflow

En üst seviyedeki iş hedefidir.

Birden fazla Capability çalıştırabilir.

---

### Single Analysis Workflow

Tek bir analitik motor çalıştırır.

Örnek:

- Forecast
- Simulation
- Supplier

---

### Composite Workflow

Birden fazla Capability'nin birlikte çalıştırıldığı Workflow'dur.

Örnek:

Forecast

↓

Safety Stock

↓

Simulation

↓

Decision Intelligence

---

### Internal Workflow

Sistem tarafından otomatik oluşturulan Workflow'lardır.

Kullanıcı tarafından doğrudan başlatılamaz.

Örnekler;

- Learning Update
- Artifact Generation
- Background Validation

---

## 7. OFFICIAL WORKFLOW FLOW

Workflow aşağıdaki resmi akış ile çalışır.

```
Business Objective
        │
        ▼
Workflow Creation
        │
        ▼
Capability Selection
        │
        ▼
Dependency Resolution
        │
        ▼
Execution Planning
        │
        ▼
Workflow Dispatch
        │
        ▼
Workflow Engine
```

Bu akışın hiçbir adımı atlanamaz.

---

## 8. WORKFLOW PRINCIPLES

Workflow aşağıdaki prensiplere uymak zorundadır.

### W1

Single Entry

Her Workflow yalnızca Workflow Dispatcher üzerinden başlatılır.

---

### W2

Deterministic Planning

Aynı Objective,

aynı veri,

aynı parametre

aynı Workflow planını üretmelidir.

---

### W3

Dependency Awareness

Capability bağımlılıkları göz ardı edilemez.

---

### W4

Execution Independence

Workflow,

analitik motorların iç çalışma mantığını bilmez.

---

### W5

Capability Driven

Workflow,

Capability'leri yönetir.

Capability'lerin nasıl çalışacağını yönetmez.

---

### W6

Extensible

Yeni Capability eklemek mevcut Workflow mantığını bozmaz.

Yeni Capability yalnızca Capability Registry üzerinden sisteme eklenir.

---

## PART 01 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Workflow Definition | ✅ Complete |
| Workflow Responsibilities | ✅ Complete |
| Workflow Lifecycle | ✅ Complete |
| Workflow Types | ✅ Complete |
| Workflow Principles | ✅ Complete |
| Official Workflow Flow | ✅ Complete |

---

**DOCUMENT 03 — PART 01 COMPLETE**

# PART 02 — WORKFLOW DISPATCHER & PLANNING

---

# 9. PURPOSE OF THE WORKFLOW DISPATCHER

Workflow Dispatcher;

Application Layer ile Workflow Engine arasındaki resmi geçiş noktasıdır.

Hiçbir API Endpoint,

hiçbir Service,

hiçbir Controller,

Workflow Engine'i doğrudan çalıştıramaz.

Workflow Engine yalnızca Workflow Dispatcher tarafından başlatılabilir.

Bu kural sistem genelinde zorunludur.

---

# 10. OFFICIAL POSITION IN THE ARCHITECTURE

Workflow Dispatcher aşağıdaki katmanda bulunur.

Client

↓

API Layer

↓

Application Layer

↓

Workflow Dispatcher

↓

Workflow Engine

↓

Orchestrator

↓

Capability Engines

↓

Learning

↓

Decision Intelligence

Dispatcher;

Execution Engine'in bir parçası değildir.

Dispatcher;

Application Layer'ın resmi bileşenidir.

---

# 11. RESPONSIBILITIES

Workflow Dispatcher aşağıdaki görevlerden sorumludur.

• Business Objective kabul etmek

• Workflow oluşturmak

• Capability listesini hazırlamak

• Dependency çözümlemek

• Execution Plan üretmek

• Workflow Engine'i başlatmak

• Execution Id oluşturmak

• Trace bilgisini aktarmak

• Workflow sonucunu Application Layer'a döndürmek

Dispatcher;

analitik hesaplama yapmaz.

Dispatcher;

iş kararı üretmez.

Dispatcher;

repository erişimi yapmaz.

---

# 12. INPUT CONTRACT

Workflow Dispatcher aşağıdaki bilgileri kabul eder.

Mandatory

• Company

• User

• Business Objective

• Dataset

Optional

• Parameters

• Execution Options

• Priority

• Metadata

Dispatcher eksik zorunlu bilgi ile Workflow oluşturamaz.

---

# 13. OUTPUT CONTRACT

Dispatcher aşağıdaki çıktıları üretir.

Execution ID

Workflow ID

Execution Context

Execution Plan

Workflow Status

Estimated Capabilities

Dispatcher analiz sonucu üretmez.

Analiz çıktısı yalnızca Workflow Engine tarafından oluşturulur.

---

# 14. WORKFLOW PLANNING

Workflow Planning;

Business Objective'nin çalıştırılabilir plana dönüştürülmesidir.

Planning aşamasında;

Business Objective

↓

Capability Selection

↓

Dependency Resolution

↓

Execution Ordering

↓

Execution Plan

oluşturulur.

Planning sırasında hiçbir analiz motoru çalıştırılmaz.

---

# 15. CAPABILITY SELECTION

Workflow yalnızca gerekli Capability'leri seçer.

Örnek

Business Objective

↓

"Inventory Optimization"

↓

Required Capabilities

Forecast

Safety Stock

Simulation

Decision Intelligence

Learning

Artifact

Workflow;

gereksiz Capability çalıştırmaz.

---

# 16. DEPENDENCY RESOLUTION

Capability bağımlılıkları Planning aşamasında çözülür.

Örnek

Forecast

↓

Safety Stock

↓

Simulation

↓

Decision Intelligence

Forecast başarısız ise

Safety Stock çalıştırılamaz.

Dependency sırası Workflow tarafından korunur.

---

# 17. EXECUTION PLAN

Planning sonunda resmi Execution Plan oluşturulur.

Execution Plan aşağıdaki bilgileri içerir.

• Workflow ID

• Objective

• Capability List

• Dependency Graph

• Execution Order

• Retry Policy

• Timeout Policy

• Priority

Execution Plan immutable'dır.

Execution başladıktan sonra değiştirilemez.

---

# 18. DISPATCH RULES

Workflow Dispatcher aşağıdaki kuralları uygular.

### WD-001

Workflow yalnızca bir kez Dispatch edilir.

---

### WD-002

Execution başlamadan önce Plan tamamlanmalıdır.

---

### WD-003

Dependency çözülmeden Execution başlatılamaz.

---

### WD-004

Dispatcher hiçbir Capability'nin iç mantığını bilmez.

---

### WD-005

Dispatcher yalnızca Workflow Engine ile konuşur.

Analytical Engine'lerle doğrudan iletişim kuramaz.

---

### WD-006

Dispatcher hiçbir Business Rule içermez.

Business Rules yalnızca Capability katmanında bulunur.

---

# 19. OFFICIAL DISPATCH FLOW

Business Objective

↓

Application Command

↓

Workflow Dispatcher

↓

Workflow Planning

↓

Execution Plan

↓

Workflow Engine

↓

Execution Context

↓

Orchestrator

↓

Capabilities

---

# PART 02 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Workflow Dispatcher | ✅ Complete |
| Workflow Planning | ✅ Complete |
| Capability Selection | ✅ Complete |
| Dependency Resolution | ✅ Complete |
| Execution Plan | ✅ Complete |
| Dispatch Rules | ✅ Complete |

---

**DOCUMENT 03 — PART 02 COMPLETE**

# PART 03 — EXECUTION CONTEXT & EXECUTION LIFECYCLE

---

# 20. PURPOSE

Execution Context;

bir Workflow çalışmasının yaşamı boyunca ihtiyaç duyduğu tüm çalışma bilgisini taşıyan resmi çalışma nesnesidir.

Execution Context;

Workflow'un hafızasıdır.

Hiçbir Capability kendi Execution Context'ini oluşturamaz.

Execution Context yalnızca Workflow Engine tarafından oluşturulur.

---

# 21. EXECUTION CONTEXT RESPONSIBILITIES

Execution Context aşağıdaki bilgileri taşır.

• Execution ID

• Workflow ID

• Company ID

• User ID

• Dataset ID

• Business Objective

• Selected Capabilities

• Parameters

• Runtime Metadata

• Trace Information

• Execution Status

Execution Context hesaplama yapmaz.

Execution Context yalnızca çalışma bilgisini taşır.

---

# 22. EXECUTION ID

Her Execution benzersiz bir kimlik taşır.

Kurallar

• Global olarak benzersiz olmalıdır.

• Workflow boyunca değiştirilemez.

• Tekrar kullanılamaz.

• Immutable'dır.

Execution ID sistemdeki tüm logların ortak anahtarıdır.

---

# 23. EXECUTION STATUS

Her Execution aşağıdaki durumlardan yalnızca birinde bulunabilir.

Created

Validated

Planned

Queued

Running

Completed

Failed

Cancelled

Timeout

Execution aynı anda birden fazla durumda olamaz.

---

# 24. EXECUTION STATE TRANSITIONS

Resmi geçişler aşağıdaki gibidir.

Created

↓

Validated

↓

Planned

↓

Queued

↓

Running

↓

Completed

Alternatif geçişler

Running

↓

Failed

Running

↓

Cancelled

Running

↓

Timeout

Completed durumundan başka bir duruma geçilemez.

---

# 25. EXECUTION METADATA

Execution Metadata aşağıdaki bilgileri içerir.

• Creation Time

• Start Time

• Finish Time

• Duration

• Retry Count

• Priority

• Runtime Version

• Engine Version

• Company

• User

Metadata analiz sonucu değildir.

Metadata yalnızca çalışma bilgisi içerir.

---

# 26. TRACE CONTEXT

Execution boyunca tüm işlemler aynı Trace Context altında yürütülür.

Trace Context aşağıdaki alanları içerir.

• Trace ID

• Correlation ID

• Parent Execution

• Request Source

• API Version

• Client Version

Trace Context sistem genelinde değiştirilemez.

---

# 27. EXECUTION PARAMETERS

Execution aşağıdaki parametreleri taşıyabilir.

Mandatory

• Dataset

• Objective

Optional

• Forecast Method

• Simulation Count

• Confidence Level

• Planning Horizon

• Custom Parameters

Capability yalnızca kendisine ait parametreleri kullanabilir.

---

# 28. EXECUTION RESULT

Execution tamamlandığında resmi Execution Result oluşturulur.

Execution Result aşağıdaki bilgileri içerir.

• Execution Status

• Produced Artifacts

• Produced Events

• Warnings

• Errors

• Metrics

• Runtime Statistics

Execution Result doğrudan API Response değildir.

---

# 29. EXECUTION PRINCIPLES

### EX-001

Execution Context immutable'dır.

---

### EX-002

Execution Status yalnızca Workflow Engine tarafından değiştirilebilir.

---

### EX-003

Capability Execution Context'i değiştiremez.

---

### EX-004

Execution Metadata çalışma sırasında genişletilebilir ancak mevcut alanlar değiştirilemez.

---

### EX-005

Execution Result yalnızca Execution tamamlandıktan sonra oluşturulur.

---

### EX-006

Execution başarısız olsa bile Trace bilgisi korunmalıdır.

---

# 30. OFFICIAL EXECUTION FLOW

Workflow Dispatcher

↓

Execution Context Creation

↓

Workflow Engine

↓

Capability Execution

↓

Learning

↓

Decision Intelligence

↓

Artifact Generation

↓

Execution Result

↓

Application Layer

---

# PART 03 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Execution Context | ✅ Complete |
| Execution Status | ✅ Complete |
| Execution Lifecycle | ✅ Complete |
| Execution Metadata | ✅ Complete |
| Trace Context | ✅ Complete |
| Execution Result | ✅ Complete |

---

**DOCUMENT 03 — PART 03 COMPLETE**

# PART 04 — CAPABILITY ORCHESTRATION

---

# 31. PURPOSE

Capability Orchestration;

Business Objective'nin gerçekleştirilmesi için gerekli tüm Capability'lerin
doğru sırada,
doğru bağımlılıklarla,
kontrollü şekilde çalıştırılmasını sağlayan resmi mekanizmadır.

Capability Orchestration;

iş kararı üretmez.

Analiz hesaplamaz.

Workflow yönetmez.

Yalnızca Capability yaşam döngüsünü yönetir.

---

# 32. CAPABILITY DEFINITION

Capability;

tek bir iş yeteneğini yerine getiren bağımsız yürütülebilir modüldür.

Örnek Capability'ler

• Forecast

• Safety Stock

• Simulation

• Supplier Analysis

• Backtest

• Learning

• Decision Intelligence

• Artifact Generation

Her Capability tek bir sorumluluğa sahiptir.

---

# 33. CAPABILITY PRINCIPLES

Platformdaki tüm Capability'ler aşağıdaki kurallara uymak zorundadır.

### CAP-001

Single Responsibility

Her Capability yalnızca tek bir iş yeteneğini gerçekleştirir.

---

### CAP-002

Isolation

Capability kendi çalışma alanı dışında hiçbir veriyi değiştiremez.

---

### CAP-003

Independent Execution

Capability mümkün olduğu sürece bağımsız çalışabilmelidir.

---

### CAP-004

Deterministic

Aynı giriş verisi aynı çıktıyı üretmelidir.

---

### CAP-005

Observable

Her Capability çalışma sürecini loglamak zorundadır.

---

### CAP-006

Composable

Capability'ler farklı Workflow'larda tekrar kullanılabilir olmalıdır.

---

# 34. OFFICIAL CAPABILITY LIST

Document 03 kapsamında tanımlanan resmi Capability'ler aşağıdaki gibidir.

Core Analysis

• Forecast

• Safety Stock

• Simulation

• Supplier

• Backtest

AI Layer

• Learning

• Decision Intelligence

Infrastructure

• Artifact Generation

• Event Publishing

• Notification

Yeni Capability yalnızca Capability Registry üzerinden sisteme eklenebilir.

---

# 35. CAPABILITY REGISTRY

Capability Registry;

platformdaki tüm Capability'lerin resmi kayıt noktasıdır.

Registry aşağıdaki bilgileri saklar.

• Capability Name

• Version

• Owner

• Required Inputs

• Optional Inputs

• Produced Outputs

• Dependency List

• Health Status

Workflow yalnızca Registry'de bulunan Capability'leri çalıştırabilir.

---

# 36. REQUIRED VS OPTIONAL CAPABILITIES

Capability'ler iki gruba ayrılır.

### Required Capability

Business Objective'nin tamamlanabilmesi için zorunludur.

Başarısız olması Workflow'u durdurabilir.

Örnek

Forecast

↓

Safety Stock

---

### Optional Capability

Business Objective'yi zenginleştirir.

Başarısız olması Workflow'u durdurmaz.

Örnek

Learning

Narrative

Artifact Explainability

---

Bu ayrım sistem genelinde zorunludur.

---

# 37. CAPABILITY DEPENDENCY GRAPH

Capability'ler birbirine bağımlı olabilir.

Örnek

Forecast

↓

Safety Stock

↓

Simulation

↓

Decision Intelligence

↓

Artifact

Dependency Graph çalışma zamanında değiştirilemez.

---

# 38. GRACEFUL DEGRADATION

Platform aşağıdaki prensibi uygular.

Optional Capability başarısız olursa;

Workflow devam eder.

Sistem mevcut sonuçlarla çalışmasını sürdürür.

Örnek

Forecast

↓

Safety Stock

↓

Simulation

↓

Learning ❌

↓

Decision Intelligence ✅

Learning başarısız olduğu halde

Decision Intelligence çalışmaya devam eder.

---

Required Capability başarısız olursa;

ilgili bağımlı Capability'ler çalıştırılmaz.

---

# 39. CAPABILITY EXECUTION ORDER

Execution sırası yalnızca Dependency Graph tarafından belirlenir.

Hiçbir Capability kendi sırasını değiştiremez.

Execution Order

Forecast

↓

Safety Stock

↓

Simulation

↓

Supplier

↓

Backtest

↓

Learning

↓

Decision Intelligence

↓

Artifact

↓

Events

---

# 40. CAPABILITY CONTRACT

Her Capability aşağıdaki sözleşmeye uymak zorundadır.

Input

↓

Validate

↓

Execute

↓

Produce Result

↓

Publish Metadata

↓

Return Capability Result

Capability doğrudan API Response oluşturamaz.

Capability Repository erişimini kendi başına yönetemez.

---

# 41. CAPABILITY RESULT

Her Capability aşağıdaki çıktıları üretir.

• Status

• Output

• Metrics

• Runtime

• Warnings

• Errors

Capability Result,

Execution Result değildir.

Execution Result,

Capability Result'ların birleşimidir.

---

# 42. CAPABILITY ORCHESTRATION FLOW

Workflow Engine

↓

Capability Registry

↓

Dependency Resolution

↓

Execution Scheduler

↓

Capability Execution

↓

Capability Results

↓

Execution Result

---

# PART 04 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Capability Definition | ✅ Complete |
| Capability Registry | ✅ Complete |
| Dependency Graph | ✅ Complete |
| Required / Optional | ✅ Complete |
| Graceful Degradation | ✅ Complete |
| Capability Contract | ✅ Complete |

---

**DOCUMENT 03 — PART 04 COMPLETE**

# PART 05 — EXECUTION POLICIES & SCHEDULING

---

# 43. PURPOSE

Execution Policy;

Workflow Engine'in Execution süresince uygulayacağı çalışma kurallarını tanımlar.

Bu kurallar;

- güvenilirliği,
- tekrar edilebilirliği,
- kaynak kullanımını,
- hata yönetimini

standart hale getirir.

Execution Policy tüm Workflow'lar için zorunludur.

---

# 44. EXECUTION POLICY PRINCIPLES

Execution Policy aşağıdaki prensiplere uyar.

### EP-001

Predictable

Her Workflow aynı koşullarda aynı politika ile çalıştırılır.

---

### EP-002

Recoverable

Başarısız Execution uygun olduğunda tekrar başlatılabilir.

---

### EP-003

Observable

Tüm Policy kararları loglanmalıdır.

---

### EP-004

Configurable

Politikalar merkezi olarak yönetilebilir olmalıdır.

---

### EP-005

Non-Intrusive

Policy, Capability'nin iş mantığını değiştiremez.

---

# 45. EXECUTION PRIORITY

Workflow aşağıdaki öncelik seviyelerini destekler.

Critical

High

Normal

Low

Background

Priority yalnızca Execution sırasını etkiler.

Analiz sonucunu etkilemez.

---

# 46. EXECUTION QUEUE

Workflow Engine tüm Execution'ları resmi kuyruğa alır.

Execution sırası aşağıdaki kriterlere göre belirlenebilir.

• Priority

• Submission Time

• Company Policy

• Resource Availability

Queue sırası çalışma sırasında manuel değiştirilemez.

---

# 47. PARALLEL EXECUTION

Bağımsız Capability'ler aynı anda çalıştırılabilir.

Örnek

Forecast

↓

Safety Stock

↓

Simulation

↓

┌───────────────┐

Supplier

Learning

└───────────────┘

↓

Decision Intelligence

Dependency bulunan Capability'ler paralel çalıştırılamaz.

---

# 48. SERIAL EXECUTION

Aşağıdaki durumlarda sıralı çalışma zorunludur.

• Dependency mevcutsa

• Shared Resource kullanılıyorsa

• Business Rule gerektiriyorsa

Workflow Engine bu kuralları ihlal edemez.

---

# 49. RETRY POLICY

Retry yalnızca Retry Policy tarafından yönetilir.

Retry aşağıdaki nedenlerle uygulanabilir.

• Temporary Network Error

• Timeout

• External Service Failure

• Retryable Infrastructure Error

Retry;

Business Validation Error durumunda uygulanmaz.

---

# 50. TIMEOUT POLICY

Her Capability maksimum çalışma süresine sahiptir.

Timeout oluşursa;

Capability

↓

Failed

↓

Workflow Policy değerlendirilir.

Optional Capability ise Workflow devam edebilir.

Required Capability ise Workflow sonlandırılabilir.

---

# 51. CANCELLATION POLICY

Execution aşağıdaki nedenlerle iptal edilebilir.

• User Request

• Company Policy

• Resource Limitation

• Administrative Action

Cancelled Execution yeniden başlatılamaz.

Yeni Execution oluşturulmalıdır.

---

# 52. RESOURCE MANAGEMENT

Workflow Engine aşağıdaki kaynakları yönetir.

• CPU

• Memory

• Worker

• Queue Slot

• AI Session

• Database Connection

Hiçbir Capability sistem kaynaklarını sınırsız kullanamaz.

---

# 53. CONCURRENCY RULES

Bir Dataset üzerinde aynı anda birden fazla çakışan Execution çalıştırılması sistem politikalarına bağlıdır.

Sistem aşağıdaki stratejileri destekleyebilir.

• Reject

• Queue

• Merge

• Replace

Bu davranış Company Policy tarafından belirlenebilir.

---

# 54. FAILURE POLICY

Capability başarısız olduğunda Workflow aşağıdaki kararlardan yalnızca birini uygular.

Continue

Retry

Skip

Abort

Fallback

Karar Dependency ve Capability tipine göre verilir.

---

# 55. OFFICIAL EXECUTION POLICY FLOW

Workflow

↓

Priority Assignment

↓

Queue

↓

Resource Allocation

↓

Execution

↓

Policy Evaluation

↓

Retry / Continue / Abort

↓

Execution Result

---

# 56. EXECUTION POLICY PRINCIPLES

Workflow Engine aşağıdaki kuralları uygular.

### POL-001

Execution hiçbir zaman Queue dışından başlayamaz.

---

### POL-002

Retry yalnızca Policy tarafından başlatılır.

---

### POL-003

Timeout sistem tarafından yönetilir.

---

### POL-004

Capability kendi Retry kararını veremez.

---

### POL-005

Cancellation merkezi olarak yönetilir.

---

### POL-006

Resource Allocation yalnızca Workflow Engine tarafından yapılır.

---

# PART 05 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Execution Priority | ✅ Complete |
| Queue Management | ✅ Complete |
| Parallel Execution | ✅ Complete |
| Retry Policy | ✅ Complete |
| Timeout Policy | ✅ Complete |
| Cancellation Policy | ✅ Complete |
| Resource Management | ✅ Complete |
| Failure Policy | ✅ Complete |

---

**DOCUMENT 03 — PART 05 COMPLETE**

# PART 06 — WORKFLOW MONITORING, RECOVERY & OBSERVABILITY

---

# 57. PURPOSE

Workflow Monitoring;

Workflow Execution sürecinin gerçek zamanlı olarak izlenmesini,
ölçülmesini,
raporlanmasını
ve gerektiğinde kurtarma (Recovery) işlemlerinin başlatılmasını sağlayan resmi mekanizmadır.

Monitoring;

Execution'ın bir parçası değildir.

Monitoring;

Execution hakkında bilgi üretir.

---

# 58. OBSERVABILITY PRINCIPLES

Platform aşağıdaki üç temel Observability bileşenini destekler.

• Logs

• Metrics

• Traces

Bu üç bileşen birlikte sistemin çalışma durumunu gösterir.

---

# 59. LOGGING

Her Workflow aşağıdaki olayları loglamak zorundadır.

• Workflow Created

• Workflow Planned

• Workflow Started

• Capability Started

• Capability Finished

• Capability Failed

• Retry Started

• Retry Completed

• Workflow Completed

• Workflow Failed

Log kayıtları silinemez.

---

# 60. METRICS

Workflow aşağıdaki metrikleri üretmelidir.

Execution Duration

Planning Duration

Capability Duration

Queue Waiting Time

Retry Count

Failure Count

Success Rate

Average Runtime

Metrics yalnızca ölçüm amacıyla kullanılır.

---

# 61. TRACEABILITY

Her Execution tek bir Trace altında yürütülür.

Trace aşağıdaki ilişkileri korur.

Request

↓

Workflow

↓

Capabilities

↓

Learning

↓

Decision Intelligence

↓

Artifacts

↓

Events

Bu zincir hiçbir noktada kopamaz.

---

# 62. HEALTH MONITORING

Workflow Engine aşağıdaki bileşenlerin sağlık durumunu izler.

Workflow Engine

Orchestrator

Capability Registry

Execution Queue

Learning Engine

Decision Intelligence

Artifact Service

Health durumu aşağıdaki seviyelerde raporlanır.

Healthy

Warning

Critical

Unavailable

---

# 63. FAILURE DETECTION

Monitoring aşağıdaki hata türlerini tespit eder.

Capability Failure

Timeout

Dependency Failure

Infrastructure Failure

Resource Exhaustion

Unexpected Exception

Her hata resmi Error Catalog ile eşleştirilir.

---

# 64. RECOVERY POLICY

Recovery yalnızca sistem politikaları kapsamında uygulanabilir.

Recovery stratejileri.

Retry

Resume

Restart

Fallback

Abort

Recovery kararı Capability tarafından verilemez.

Workflow Engine tarafından uygulanır.

---

# 65. AUDITABILITY

Workflow aşağıdaki bilgileri denetlenebilir şekilde saklar.

Execution ID

Workflow ID

Capability Order

User

Company

Dataset

Parameters

Execution Time

Result Status

Audit kayıtları değiştirilemez.

---

# 66. WORKFLOW HISTORY

Her Workflow geçmişi saklanmalıdır.

Workflow geçmişi aşağıdaki amaçlarla kullanılabilir.

Operational Audit

Backtest

Learning

Performance Analysis

Root Cause Analysis

---

# 67. OFFICIAL OBSERVABILITY FLOW

Workflow

↓

Logs

↓

Metrics

↓

Traces

↓

Health

↓

Recovery

↓

Audit

↓

History

---

# 68. OBSERVABILITY PRINCIPLES

### OBS-001

Hiçbir Workflow logsuz çalışamaz.

---

### OBS-002

Her Capability kendi Runtime bilgisini üretmelidir.

---

### OBS-003

Trace ID tüm Workflow boyunca korunmalıdır.

---

### OBS-004

Monitoring iş mantığını değiştiremez.

---

### OBS-005

Recovery yalnızca Workflow Engine tarafından başlatılır.

---

### OBS-006

Audit kayıtları immutable'dır.

---

# PART 06 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Logging | ✅ Complete |
| Metrics | ✅ Complete |
| Traceability | ✅ Complete |
| Health Monitoring | ✅ Complete |
| Recovery | ✅ Complete |
| Audit | ✅ Complete |
| Workflow History | ✅ Complete |

---

**DOCUMENT 03 — PART 06 COMPLETE**

# PART 07 — WORKFLOW GOVERNANCE & ARCHITECTURAL COMPLIANCE

---

# 69. PURPOSE

Bu bölüm;

Workflow Architecture'nin uzun vadeli sürdürülebilirliğini sağlamak,

gelecekte yapılacak geliştirmelerin ortak kurallara uygun ilerlemesini garanti altına almak amacıyla hazırlanmıştır.

Bu bölümde tanımlanan kurallar tüm Workflow bileşenleri için bağlayıcıdır.

---

# 70. ARCHITECTURAL INVARIANTS

Aşağıdaki kurallar hiçbir sürümde değiştirilemez.

### INV-001

Her Workflow yalnızca bir Business Objective'ye bağlıdır.

---

### INV-002

Her Execution yalnızca tek bir Workflow tarafından oluşturulur.

---

### INV-003

Workflow Engine doğrudan API tarafından çağrılamaz.

---

### INV-004

Capability'ler yalnızca Workflow Engine tarafından çalıştırılır.

---

### INV-005

Execution Context yalnızca Workflow Engine tarafından oluşturulur.

---

### INV-006

Decision Intelligence yalnızca tamamlanmış analiz sonuçlarını kullanır.

---

# 71. FORBIDDEN BEHAVIORS

Aşağıdaki davranışlar sistem genelinde yasaktır.

• API Endpoint'in doğrudan Analytical Engine çağırması

• Capability'nin başka bir Capability'yi doğrudan çalıştırması

• Capability'nin Execution Context'i değiştirmesi

• Workflow dışında Capability sırası oluşturulması

• Repository erişiminin Workflow tarafından yapılması

• Decision Intelligence'ın analiz başlatması

• Learning Engine'in Workflow yönetmesi

Bu davranışlar mimari ihlal olarak değerlendirilir.

---

# 72. EXTENSION RULES

Yeni Capability eklenirken aşağıdaki kurallar uygulanmalıdır.

Yeni Capability;

• Registry'ye kayıt edilmelidir.

• Input Contract tanımlanmalıdır.

• Output Contract tanımlanmalıdır.

• Dependency List oluşturulmalıdır.

• Required / Optional sınıflandırması yapılmalıdır.

• Health Check desteklemelidir.

• Runtime Metrics üretmelidir.

---

# 73. BACKWARD COMPATIBILITY

Workflow Architecture geriye dönük uyumluluğu korumalıdır.

Yeni sürümler;

mevcut Workflow tanımlarını geçersiz kılamaz.

Zorunlu kırıcı değişiklikler yalnızca yeni Major Version ile yapılabilir.

---

# 74. VERSIONING

Workflow aşağıdaki sürümleme kurallarını kullanır.

Major

Mimariyi değiştiren değişiklikler

Minor

Yeni Capability eklenmesi

Patch

Hata düzeltmeleri

Workflow Version,

Execution Metadata içerisinde saklanmalıdır.

---

# 75. COMPLIANCE REQUIREMENTS

Workflow bileşenleri aşağıdaki gereksinimleri sağlamalıdır.

• Document 01 Foundation

• Document 02 Domain Model

• Document 03 Workflow Architecture

Hiçbir yeni geliştirme bu üç dokümanla çelişemez.

---

# 76. VALIDATION CHECKLIST

Yeni bir Workflow bileşeni eklenmeden önce aşağıdaki sorular cevaplanmalıdır.

□ Business Objective tanımlı mı?

□ Capability Registry güncellendi mi?

□ Dependency Graph oluşturuldu mu?

□ Required / Optional sınıflandırması yapıldı mı?

□ Execution Policy tanımlandı mı?

□ Monitoring desteği var mı?

□ Audit desteği var mı?

□ Metrics üretiyor mu?

□ Error Catalog ile uyumlu mu?

□ Document 03 kurallarına uygun mu?

---

# 77. IMPLEMENTATION GUIDELINES

Kod geliştirme sırasında aşağıdaki sıra izlenmelidir.

Business Objective

↓

Workflow

↓

Execution

↓

Capabilities

↓

Learning

↓

Decision Intelligence

↓

Artifacts

↓

Events

↓

API Response

Bu sıra değiştirilemez.

---

# 78. DOCUMENT RELATIONSHIPS

Workflow Architecture aşağıdaki dokümanlara bağlıdır.

Previous Documents

• Document 01 — Foundation

• Document 02 — Domain Model

Next Documents

• Document 04 — Execution Engine

• Document 05 — AI Decision Intelligence

• Document 06 — Data Architecture

• Document 07 — Application Architecture

---

# 79. ARCHITECTURE FREEZE

Bu doküman;

Workflow katmanı için resmi referans mimaridir.

Workflow ile ilgili yapılacak tüm geliştirmeler bu dokümanı referans almak zorundadır.

Bu dokümanda tanımlanan mimari kurallar;

Architecture Decision Record (ADR) oluşturulmadan değiştirilemez.

---

# PART 07 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Architectural Invariants | ✅ Complete |
| Forbidden Behaviors | ✅ Complete |
| Extension Rules | ✅ Complete |
| Compatibility Rules | ✅ Complete |
| Governance | ✅ Complete |
| Validation Checklist | ✅ Complete |
| Architecture Freeze | ✅ Complete |

---

# DOCUMENT 03 COMPLETION STATUS

| Part | Status |
|------|--------|
| Part 01 — Workflow Foundation | ✅ Complete |
| Part 02 — Workflow Dispatcher & Planning | ✅ Complete |
| Part 03 — Execution Context & Lifecycle | ✅ Complete |
| Part 04 — Capability Orchestration | ✅ Complete |
| Part 05 — Execution Policies & Scheduling | ✅ Complete |
| Part 06 — Workflow Monitoring, Recovery & Observability | ✅ Complete |
| Part 07 — Workflow Governance & Architectural Compliance | ✅ Complete |

---

# DOCUMENT 03 STATUS

**Architecture Freeze Candidate**

Version: **2.0**

Status: **Complete**

Next Document:

**DOCUMENT_04_EXECUTION_ENGINE.md**

# Revision — Product Architecture Phase 1

- **Revision date:** 2026-08-06
- **Revision status:** BINDING
- **ADR reference:** ADR-020

This revision supersedes only the conflicting interpretation of historical INV-001; it does not delete the historical text. Every Workflow belongs to exactly one Execution Intent. An Execution Intent is exactly one of Business Objective or Single Analysis Capability: `objective_type XOR analysis_type`.

A Single Analysis Workflow runs exactly one analytical capability, has no hidden analytical prerequisite, and is not automatically expanded into a Business Objective. Learning may run as its post-analysis learning stage. Decision Intelligence does not run.

A Business Objective Workflow runs one or more ordered analytical capabilities and its required dependencies are binding. Forecast and Safety Stock Business Workflow sequences are defined by the Document 02 Product Architecture revision. Learning runs after analytical validation; Decision Intelligence creates the final operational decision; the Dynamic Operational Plan is produced before the final AI Artifact.

