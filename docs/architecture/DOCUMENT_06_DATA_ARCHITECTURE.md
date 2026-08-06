# STOKONOMI ARCHITECTURE SPECIFICATION v2.0

# DOCUMENT 06

# DATA ARCHITECTURE

Version: 2.0

Status: Draft → Architecture Freeze Candidate

Priority: Mandatory

Scope:
Operational Data
Execution Data
Knowledge Data
Memory Store
Artifact Store
Metadata
Data Governance

---

# PART 01 — DATA ARCHITECTURE FOUNDATION

---

# 1. PURPOSE

Bu doküman;

Stokonomi Platformu içerisinde üretilen,

işlenen,

öğrenilen,

ve saklanan

tüm verilerin resmi mimarisini tanımlar.

Bu mimari;

yalnızca veritabanını değil,

Platform'un tüm bilgi yaşam döngüsünü kapsar.

---

# 2. OFFICIAL DEFINITION

Data Architecture;

Operational Data,

Execution Data,

Knowledge Data,

AI Memory,

Artifact Data

ve

Metadata katmanlarının birlikte oluşturduğu resmi veri mimarisidir.

Bu mimari;

Platform içerisindeki tüm veri akışlarının temelidir.

---

# 3. DATA PHILOSOPHY

Platform veriyi yalnızca saklamaz.

Veriyi;

oluşturur,

doğrular,

zenginleştirir,

öğrenir,

ilişkilendirir,

ve yeniden kullanır.

Bu nedenle veri,

Platform'un temel varlığıdır.

---

# 4. DATA LIFECYCLE

Platform verisi aşağıdaki yaşam döngüsünü izler.

Raw Data

↓

Validated Data

↓

Operational Data

↓

Execution Data

↓

Knowledge Data

↓

AI Memory

↓

Decision Data

↓

Artifact

↓

Archive

Hiçbir veri doğrulanmadan üst katmana geçemez.

---

# 5. DATA LAYERS

Platform aşağıdaki resmi veri katmanlarını kullanır.

• Operational Data

• Execution Data

• Intelligence Data

• Memory Store

• Artifact Store

• Metadata Store

• Audit Store

Bu katmanlar birbirinden bağımsızdır.

---

# 6. DATA OWNERSHIP

Her veri yalnızca tek bir katmanın sahipliğindedir.

Örnek.

Dataset

↓

Operational Layer

Execution Result

↓

Execution Layer

Company Memory

↓

Intelligence Layer

Artifact

↓

Artifact Layer

Ownership değiştirilemez.

---

# 7. DATA FLOW

Platform veri akışı aşağıdaki sırayı takip eder.

Client

↓

Dataset

↓

Validation

↓

Execution

↓

Learning

↓

Decision

↓

Artifact

↓

Storage

↓

API Response

Bu akış sistem genelinde standarttır.

---

# 8. DATA PRINCIPLES

### DATA-001

Her veri tek bir resmi kaynağa sahip olmalıdır.

---

### DATA-002

Ham veri değiştirilemez.

---

### DATA-003

Operational Data ile AI Memory ayrıdır.

---

### DATA-004

Knowledge Data yalnızca Learning tarafından oluşturulur.

---

### DATA-005

Execution Data yalnızca Execution Engine tarafından oluşturulur.

---

### DATA-006

Her veri yaşam döngüsü izlenebilir olmalıdır.

---

# 9. DATA CLASSIFICATION

Platform verileri aşağıdaki şekilde sınıflandırılır.

Operational

Analytical

Intelligence

Knowledge

Metadata

Artifact

Audit

Temporary

Bu sınıflandırma sistem genelinde standarttır.

---

# 10. OFFICIAL DATA FLOW

Operational Data

↓

Execution Data

↓

Knowledge Data

↓

Memory Store

↓

Decision Data

↓

Artifact Store

↓

API Layer

---

# PART 01 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Data Definition | ✅ Complete |
| Data Philosophy | ✅ Complete |
| Data Lifecycle | ✅ Complete |
| Data Layers | ✅ Complete |
| Data Ownership | ✅ Complete |
| Data Principles | ✅ Complete |

---

**DOCUMENT 06 — PART 01 COMPLETE**

# PART 02 — OPERATIONAL DATA MODEL

---

# 11. PURPOSE

Operational Data;

Platform'un günlük operasyonlarını yürüten resmi iş verisidir.

Bu katman;

müşteriden gelen veriyi,

iş kurallarını,

ve analiz girişlerini içerir.

Operational Data;

AI Knowledge değildir.

Execution Result değildir.

---

# 12. OFFICIAL DEFINITION

Operational Data;

Platform'un çalışabilmesi için gerekli olan,

işletme tarafından sağlanan,

veya işletme sistemlerinden alınan

doğrulanmış iş verisidir.

Operational Data;

Platform'un tek resmi giriş verisidir.

---

# 13. OPERATIONAL DATA SOURCES

Operational Data aşağıdaki kaynaklardan gelebilir.

• Excel Upload

• ERP Integration

• REST API

• CSV Import

• Manual Entry

• Scheduled Import

• External Business Systems

Tüm kaynaklar aynı doğrulama sürecinden geçmelidir.

---

# 14. DATA CATEGORIES

Operational Data aşağıdaki kategorilere ayrılır.

Master Data

↓

Transaction Data

↓

Planning Data

↓

Reference Data

↓

Configuration Data

↓

Operational Parameters

Her kategori farklı yaşam döngüsüne sahiptir.

---

# 15. MASTER DATA

Master Data aşağıdaki temel işletme bilgilerini içerir.

• Company

• Warehouse

• SKU

• Supplier

• Customer

• Unit Definitions

Master Data kimlik bilgisidir.

Sık değişmez.

---

# 16. TRANSACTION DATA

Transaction Data aşağıdaki operasyonel kayıtları içerir.

Demand History

Inventory History

Purchase Orders

Receipts

Issues

Returns

Transfers

Transaction Data zaman serisi oluşturur.

---

# 17. PLANNING DATA

Planning Data aşağıdaki bilgileri içerir.

Planning Horizon

Service Level Target

Lead Time

Review Period

MOQ

Order Frequency

Planning Data analizleri yönlendirir.

---

# 18. REQUIRED & OPTIONAL DATA

Platform veri alanlarını aşağıdaki şekilde sınıflandırır.

Mandatory Data

↓

Optional Data

↓

Derived Data

↓

Calculated Data

Mandatory veri olmadan ilgili analiz başlatılamaz.

Optional veri eksik olduğunda sistem uygun fallback mekanizmasını kullanmalıdır.

---

# 19. GRACEFUL DEGRADATION

Operational Data eksik olduğunda;

Platform tamamen durmaz.

Sistem;

mevcut verilerle çalışır,

eksik alanları raporlar,

ilgili AI yeteneklerini devre dışı bırakır,

ve kullanıcıyı bilgilendirir.

Hiçbir opsiyonel veri,

tüm Workflow'u durduramaz.

---

# 20. OPERATIONAL DATA PRINCIPLES

### DATA-007

Operational Data sistemin tek resmi giriş verisidir.

---

### DATA-008

Her veri doğrulanmalıdır.

---

### DATA-009

Mandatory ve Optional alanlar açıkça tanımlanmalıdır.

---

### DATA-010

Optional veri eksikliği yalnızca ilgili yeteneği etkiler.

---

### DATA-011

Türetilmiş (Derived) veriler yeniden hesaplanabilir olmalıdır.

---

### DATA-012

Operational Data AI Memory ile karıştırılamaz.

---

# OFFICIAL OPERATIONAL DATA FLOW

External Source

↓

Validation Engine

↓

Operational Data Store

↓

Execution Engine

↓

Analysis Results

↓

AI Intelligence

---

# PART 02 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Operational Data | ✅ Complete |
| Data Sources | ✅ Complete |
| Data Categories | ✅ Complete |
| Master & Transaction Data | ✅ Complete |
| Required / Optional Model | ✅ Complete |
| Graceful Degradation | ✅ Complete |

---

**DOCUMENT 06 — PART 02 COMPLETE**

# PART 03 — INTELLIGENCE DATA MODEL

---

# 21. PURPOSE

Intelligence Data;

AI Intelligence katmanı tarafından oluşturulan,

öğrenilen,

yorumlanan,

ve gelecekte tekrar kullanılacak resmi bilgi katmanıdır.

Intelligence Data;

Operational Data değildir.

Execution Data değildir.

AI tarafından üretilmiş bilgidir.

---

# 22. OFFICIAL DEFINITION

Intelligence Data;

Execution sonuçlarının,

öğrenme süreçlerinin,

davranış analizlerinin,

ve AI kararlarının oluşturduğu kurumsal bilgi katmanıdır.

Bu veri;

AI'nın uzun dönem hafızasını oluşturur.

---

# 23. INTELLIGENCE DATA COMPONENTS

Platform aşağıdaki Intelligence veri bileşenlerini kullanır.

• Company Memory

• Pattern Memory

• Decision Memory

• Knowledge Base

• Recommendation History

• Confidence History

• Learning History

Bu yapı sistem genelinde standarttır.

---

# 24. COMPANY MEMORY STORE

Company Memory aşağıdaki bilgileri saklayabilir.

Company Profile

Planning Behaviour

Inventory Behaviour

Risk Behaviour

Supplier Behaviour

Decision Behaviour

Operational Preferences

Company Memory yalnızca ilgili şirkete aittir.

---

# 25. PATTERN MEMORY STORE

Pattern Memory aşağıdaki davranış bilgilerini içerir.

Demand Pattern

Trend

Seasonality

Volatility

Intermittent Behaviour

Lead Time Behaviour

Forecast Stability

Pattern Confidence

Pattern Memory SKU bazlıdır.

---

# 26. DECISION MEMORY

Decision Memory;

geçmiş AI kararlarını saklar.

Her kayıt aşağıdaki bilgileri içerir.

Decision

↓

Reason

↓

Evidence

↓

Confidence

↓

Outcome

↓

Feedback

↓

Version

Decision Memory gelecekteki kararlar için referans oluşturabilir.

---

# 27. KNOWLEDGE BASE

Knowledge Base;

Company Learning ve Pattern Intelligence tarafından doğrulanmış bilgilerin resmi deposudur.

Knowledge;

ham veri değildir.

İşlenmiş bilgidir.

Knowledge Base yalnızca doğrulanmış bilgi içerir.

---

# 28. RECOMMENDATION HISTORY

Platform üretilen Recommendation geçmişini saklayabilir.

Recommendation

↓

Decision Version

↓

Reasoning

↓

Evidence

↓

User Response

↓

Outcome

Bu bilgiler Learning sürecine geri beslenebilir.

---

# 29. CONFIDENCE HISTORY

Platform Confidence değişimini izleyebilir.

Confidence History aşağıdaki bilgileri içerebilir.

Decision Confidence

Pattern Confidence

Learning Confidence

Recommendation Confidence

Confidence değişimi zaman içerisinde analiz edilebilir.

---

# 30. INTELLIGENCE DATA PRINCIPLES

### DATA-013

Intelligence Data yalnızca AI tarafından oluşturulur.

---

### DATA-014

Company Memory şirket bazında izole edilmelidir.

---

### DATA-015

Pattern Memory SKU bazında yönetilmelidir.

---

### DATA-016

Knowledge yalnızca doğrulanmış bilgi içerir.

---

### DATA-017

Decision Memory silinmez.

Versiyonlanır.

---

### DATA-018

Confidence geçmişi izlenebilir olmalıdır.

---

# OFFICIAL INTELLIGENCE DATA FLOW

Execution Results

↓

Company Learning

↓

Pattern Intelligence

↓

Knowledge Base

↓

Decision Memory

↓

Recommendation History

↓

Learning Evolution

---

# PART 03 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Intelligence Data | ✅ Complete |
| Company Memory Store | ✅ Complete |
| Pattern Memory Store | ✅ Complete |
| Decision Memory | ✅ Complete |
| Knowledge Base | ✅ Complete |
| Recommendation History | ✅ Complete |

---

**DOCUMENT 06 — PART 03 COMPLETE**

# PART 04 — FEATURE STORE & SEMANTIC KNOWLEDGE

---

# 31. PURPOSE

Feature Store;

Platform içerisindeki tüm AI modellerinin,

Intelligence bileşenlerinin,

ve Decision Engine'in kullandığı standart özellik (Feature) katmanıdır.

Feature Store;

ham veri değildir.

Analiz sonucu değildir.

AI tarafından kullanılabilir standart özellik deposudur.

---

# 32. OFFICIAL DEFINITION

Feature;

Operational Data,

Execution Results,

ve Intelligence Data'dan türetilen,

AI tarafından doğrudan kullanılabilen standart bilgi öğesidir.

Feature Store;

tüm Feature'ların resmi kaynağıdır.

---

# 33. FEATURE CATEGORIES

Platform aşağıdaki Feature türlerini destekler.

Statistical Features

Operational Features

Business Features

Pattern Features

Behavioral Features

Decision Features

Confidence Features

Derived Features

Yeni Feature kategorileri eklenebilir.

---

# 34. FEATURE STORE

Feature Store aşağıdaki amaçlarla kullanılır.

• AI Learning

• Pattern Detection

• Decision Support

• Recommendation

• Confidence Calculation

• Similarity Search

• Knowledge Evolution

Feature Store sistem genelinde tek resmi Feature kaynağıdır.

---

# 35. FEATURE LIFECYCLE

Her Feature aşağıdaki yaşam döngüsünü izler.

Raw Data

↓

Feature Extraction

↓

Validation

↓

Feature Store

↓

AI Consumption

↓

Evolution

↓

Version Update

Her Feature yeniden üretilebilir olmalıdır.

---

# 36. FEATURE VERSIONING

Her Feature aşağıdaki bilgilerle versiyonlanır.

Feature ID

Feature Version

Source

Creation Time

Validation Status

Confidence

Feature geçmişi korunmalıdır.

---

# 37. SEMANTIC STORE

Semantic Store;

AI'nın kavramsal benzerlikleri değerlendirebildiği resmi veri katmanıdır.

Semantic Store;

ham veri içermez.

Anlam ilişkilerini saklar.

Örnek.

Benzer SKU

Benzer Talep Davranışı

Benzer Risk Profili

Benzer Planlama Davranışı

Semantic Store gelecekte farklı teknolojilerle uygulanabilir.

---

# 38. KNOWLEDGE GRAPH

Knowledge Graph;

Platform içerisindeki Intelligence bileşenleri arasındaki ilişkileri temsil eder.

Örnek ilişkiler.

Company

↓

Warehouse

↓

Product Family

↓

SKU

↓

Supplier

↓

Pattern

↓

Decision

↓

Artifact

Knowledge Graph;

ilişkileri tanımlar.

Verinin kendisini taşımaz.

---

# 39. KNOWLEDGE RELATIONSHIPS

Platform aşağıdaki ilişki türlerini tanıyabilir.

Belongs To

Depends On

Produced By

Learns From

Influences

Similar To

Derived From

Validated By

Yeni ilişki türleri eklenebilir.

---

# 40. FEATURE & SEMANTIC PRINCIPLES

### DATA-019

Feature yalnızca doğrulanmış veriden türetilir.

---

### DATA-020

Feature yeniden üretilebilir olmalıdır.

---

### DATA-021

Semantic Store iş verisini değil,

anlam ilişkilerini saklar.

---

### DATA-022

Knowledge Graph yalnızca ilişki yönetir.

---

### DATA-023

Feature Store AI'nın tek resmi Feature kaynağıdır.

---

### DATA-024

Feature ve Operational Data birbirinden bağımsızdır.

---

# OFFICIAL FEATURE FLOW

Operational Data

↓

Execution Results

↓

Feature Extraction

↓

Feature Store

↓

Semantic Store

↓

Knowledge Graph

↓

AI Intelligence

↓

Decision Intelligence

---

# PART 04 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Feature Store | ✅ Complete |
| Feature Lifecycle | ✅ Complete |
| Semantic Store | ✅ Complete |
| Knowledge Graph | ✅ Complete |
| Relationship Model | ✅ Complete |
| Feature Principles | ✅ Complete |

---

**DOCUMENT 06 — PART 04 COMPLETE**

# PART 05 — ARTIFACT STORE & METADATA ARCHITECTURE

---

# 41. PURPOSE

Artifact Store;

Platform tarafından oluşturulan tüm resmi çıktıların,

raporların,

AI açıklamalarının,

ve analiz sonuçlarının yaşam döngüsünü yöneten resmi veri katmanıdır.

Artifact;

ham veri değildir.

Execution değildir.

AI Memory değildir.

Sonuç ürünüdür.

---

# 42. OFFICIAL DEFINITION

Artifact;

Execution Engine,

Decision Intelligence,

ve AI Intelligence tarafından üretilen,

yeniden kullanılabilir,

versiyonlanabilir,

ve paylaşılabilir resmi çıktı nesnesidir.

Artifact sistem genelinde standarttır.

---

# 43. ARTIFACT TYPES

Platform aşağıdaki Artifact türlerini destekler.

Execution Artifact

Decision Artifact

Recommendation Artifact

AI Summary

Management Report

Executive Summary

Dashboard Snapshot

Notification Package

Yeni Artifact türleri eklenebilir.

---

# 44. ARTIFACT STORE

Artifact Store aşağıdaki görevlerden sorumludur.

• Artifact saklamak

• Artifact versiyonlamak

• Artifact paylaşmak

• Artifact tekrar kullanmak

• Artifact yaşam döngüsünü yönetmek

Artifact Store yalnızca Artifact saklar.

Knowledge saklamaz.

---

# 45. ARTIFACT METADATA

Her Artifact aşağıdaki Metadata bilgilerini içerir.

Artifact ID

Artifact Type

Version

Owner

Creation Time

Source Execution

Source Decision

Language

Visibility

Retention Policy

Metadata Artifact'in ayrılmaz parçasıdır.

---

# 46. ARTIFACT LIFECYCLE

Artifact aşağıdaki yaşam döngüsünü takip eder.

Created

↓

Validated

↓

Published

↓

Consumed

↓

Archived

↓

Retired

Artifact gerektiğinde yeniden oluşturulabilir.

---

# 47. METADATA STORE

Metadata Store;

Platform içerisindeki tüm nesnelerin tanımlayıcı bilgilerini saklayan resmi katmandır.

Metadata aşağıdaki alanlarda kullanılabilir.

Execution

Workflow

Dataset

Knowledge

Decision

Artifact

Feature

Metadata iş verisi değildir.

---

# 48. AUDIT STORE

Audit Store;

Platform içerisinde gerçekleşen kritik işlemleri izler.

Örnek.

Execution Started

Decision Generated

Knowledge Updated

Artifact Published

User Action

Policy Change

Audit kayıtları değiştirilemez.

---

# 49. TRACEABILITY

Platform aşağıdaki izlenebilirlik zincirini desteklemelidir.

Dataset

↓

Execution

↓

Capability

↓

Knowledge

↓

Decision

↓

Recommendation

↓

Artifact

↓

User

Her Artifact geriye doğru izlenebilir olmalıdır.

---

# 50. ARTIFACT & METADATA PRINCIPLES

### DATA-025

Her Artifact tek bir resmi kaynağa sahip olmalıdır.

---

### DATA-026

Artifact versiyonlanmalıdır.

---

### DATA-027

Metadata iş verisi değildir.

---

### DATA-028

Audit kayıtları silinemez.

---

### DATA-029

Her Artifact izlenebilir olmalıdır.

---

### DATA-030

Artifact yeniden üretilebilir olmalıdır.

---

# OFFICIAL ARTIFACT FLOW

Execution Engine

↓

Decision Intelligence

↓

Recommendation Engine

↓

Artifact Builder

↓

Artifact Store

↓

Metadata Store

↓

Audit Store

↓

API Layer

---

# PART 05 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Artifact Store | ✅ Complete |
| Artifact Lifecycle | ✅ Complete |
| Metadata Store | ✅ Complete |
| Audit Store | ✅ Complete |
| Traceability | ✅ Complete |
| Artifact Principles | ✅ Complete |

---

**DOCUMENT 06 — PART 05 COMPLETE**

# PART 06 — DATA GOVERNANCE, INTEGRITY & LIFECYCLE MANAGEMENT

---

# 51. PURPOSE

Data Governance;

Platform içerisindeki tüm verilerin

doğru,

güvenli,

izlenebilir,

tutarlı,

versiyonlanabilir

ve yönetilebilir şekilde kullanılmasını sağlayan resmi yönetişim modelidir.

Data Governance;

yalnızca veritabanı yönetimi değildir.

Verinin tüm yaşam döngüsünü kapsar.

---

# 52. DATA GOVERNANCE RESPONSIBILITIES

Data Governance aşağıdaki görevlerden sorumludur.

• Data Ownership tanımlamak

• Data Classification uygulamak

• Versioning kurallarını yönetmek

• Retention politikalarını belirlemek

• Data Integrity sağlamak

• Data Lineage korumak

• Data Access kurallarını yönetmek

• Data Migration süreçlerini kontrol etmek

• Archive ve Retirement süreçlerini yönetmek

Data Governance iş verisi üretmez.

---

# 53. DATA OWNERSHIP MODEL

Her veri nesnesinin tek bir resmi sahibi bulunmalıdır.

Örnek:

Operational Data

↓

Operational Data Layer

Execution Result

↓

Execution Data Layer

Company Memory

↓

Company Learning

Pattern Memory

↓

Pattern Intelligence

Decision Memory

↓

Decision Intelligence

Artifact

↓

Artifact Store

Ownership belirsiz bırakılamaz.

---

# 54. DATA VERSIONING

Aşağıdaki veri türleri versiyonlanmalıdır.

• Dataset

• Workflow

• Execution Contract

• Feature

• Company Memory

• Pattern Memory

• Knowledge

• Decision

• Recommendation

• Artifact

Yeni sürüm oluşturulduğunda önceki sürüm değiştirilemez.

---

# 55. VERSION STRUCTURE

Her versiyon aşağıdaki bilgileri içermelidir.

• Object ID

• Version ID

• Previous Version

• Creation Time

• Created By

• Source

• Change Reason

• Validation Status

• Active Status

Versiyon geçmişi izlenebilir olmalıdır.

---

# 56. DATA RETENTION

Her veri sınıfı için Retention Policy tanımlanmalıdır.

Retention Policy aşağıdaki kararları içerebilir.

• Saklama süresi

• Arşivleme zamanı

• Erişim seviyesi

• Anonimleştirme gereksinimi

• Silme koşulu

• Yasal saklama zorunluluğu

Tüm veri türleri aynı saklama politikasını kullanmak zorunda değildir.

---

# 57. IMMUTABILITY RULES

Aşağıdaki veriler immutable kabul edilir.

• Raw Dataset Version

• Completed Execution Result

• Published Decision

• Published Recommendation

• Published Artifact

• Audit Record

• Event Record

Değişiklik gerektiğinde yeni versiyon oluşturulur.

---

# 58. DATA INTEGRITY

Platform aşağıdaki bütünlük kurallarını sağlamalıdır.

• Company Ownership doğrulanmalıdır.

• Foreign Reference ilişkileri geçerli olmalıdır.

• Version zinciri kopmamalıdır.

• Dataset ile Execution ilişkisi korunmalıdır.

• Decision ile Evidence ilişkisi korunmalıdır.

• Artifact ile Source Execution ilişkisi korunmalıdır.

• Audit kayıtları değiştirilememelidir.

Bütünlük ihlali olan veri yayımlanamaz.

---

# 59. DATA CONSISTENCY

Platform aşağıdaki tutarlılık seviyelerini destekler.

### Strong Consistency

Kritik kimlik ve sahiplik verileri için kullanılır.

Örnek:

Company

User

Dataset Approval

Execution Status

---

### Eventual Consistency

Asenkron zenginleştirme verileri için kullanılabilir.

Örnek:

Metrics

Semantic Index

Notification Status

Artifact Representation

Tutarlılık modeli veri türüne göre belirlenir.

---

# 60. DATA LINEAGE

Data Lineage;

bir verinin hangi kaynaklardan üretildiğini gösterir.

Resmi Lineage zinciri aşağıdaki gibidir.

Dataset

↓

Execution

↓

Capability Result

↓

Feature

↓

Knowledge

↓

Decision

↓

Recommendation

↓

Artifact

Her türetilmiş veri kendi kaynağına geri izlenebilmelidir.

---

# 61. ARTIFACT LINEAGE EXTENSION POINT

Artifact Lineage;

bir Artifact'in üretim soy ağacını temsil eder.

Örnek:

Dataset

↓

Execution

↓

Decision

↓

Recommendation

↓

Executive Summary

↓

PDF Report

Artifact Lineage zorunlu çekirdek veri modeli değildir.

Ancak resmi genişleme noktasıdır.

Uygulandığında aşağıdaki bilgileri taşımalıdır.

• Source Dataset

• Source Execution

• Source Decision

• Source Recommendation

• AI Version

• Artifact Version

• Generation Time

---

# 62. DECISION GRAPH EXTENSION POINT

Decision Graph;

AI tarafından üretilen kararların ilişkisel geçmişini temsil edebilir.

Örnek:

Decision

↓

Evidence

↓

Pattern

↓

Company Memory

↓

Risk

↓

Recommendation

↓

Outcome

Decision Graph zorunlu çekirdek bileşen değildir.

Ancak gelecekteki Intelligence gelişimi için resmi Extension Point'tir.

---

# 63. DATA VALIDATION

Veri yaşam döngüsünün her aşamasında doğrulama uygulanmalıdır.

Validation seviyeleri:

• Structural Validation

• Schema Validation

• Business Validation

• Ownership Validation

• Consistency Validation

• Quality Validation

• Intelligence Validation

Bir üst veri katmanına yalnızca doğrulanmış veri geçebilir.

---

# 64. DATA QUALITY

Platform aşağıdaki veri kalite boyutlarını izlemelidir.

• Completeness

• Accuracy

• Consistency

• Timeliness

• Validity

• Uniqueness

• Traceability

Veri kalite skoru ilgili analiz ve karar Confidence değerini etkileyebilir.

---

# 65. DATA CORRECTION

Immutable veri doğrudan düzeltilemez.

Hata tespit edildiğinde aşağıdaki süreç uygulanır.

Error Detection

↓

Correction Request

↓

New Version

↓

Validation

↓

Activation

↓

Previous Version Retained

Geçmiş veri korunur.

---

# 66. DATA DELETION

Silme işlemleri veri türüne göre yönetilir.

Platform aşağıdaki stratejileri destekleyebilir.

• Logical Deletion

• Archival

• Anonymization

• Legal Deletion

• Permanent Deletion

Audit, Event ve yayınlanmış geçmiş kayıtları normal kullanıcı işlemleriyle silinemez.

---

# 67. COMPANY DATA ISOLATION

Her Company kendi veri alanına sahiptir.

Aşağıdaki veriler Company sınırları dışına çıkamaz.

• Operational Data

• Execution Data

• Company Memory

• Pattern Memory

• Decision Memory

• Recommendation History

• Artifact

• Audit Records

Cross-Company erişim yalnızca açık ve yetkili platform politikalarıyla mümkündür.

---

# 68. DATA ACCESS CONTROL

Veri erişimi aşağıdaki bağlamlarla doğrulanmalıdır.

• Company Identity

• User Identity

• Role

• Permission

• Data Ownership

• Data Classification

• Purpose of Access

Doğrudan fiziksel depolama erişimi uygulama kullanıcılarına açılamaz.

---

# 69. DATA ENCRYPTION

Hassas veriler aşağıdaki durumlarda korunmalıdır.

### At Rest

Depolanan veri şifrelenmelidir.

### In Transit

Taşınan veri güvenli protokollerle korunmalıdır.

### In Use

Çalışma sırasında erişim yetkilendirilmelidir.

Şifreleme anahtarları iş verisinden ayrı yönetilmelidir.

---

# 70. DATA BACKUP & RECOVERY

Platform aşağıdaki veri kurtarma yeteneklerini desteklemelidir.

• Scheduled Backup

• Point-in-Time Recovery

• Version Recovery

• Artifact Recovery

• Memory Recovery

• Audit Recovery

Backup doğrulanmadan güvenilir kabul edilemez.

---

# 71. DATA MIGRATION

Data Migration aşağıdaki sıra ile yürütülmelidir.

Discovery

↓

Mapping

↓

Validation

↓

Migration

↓

Verification

↓

Activation

↓

Rollback Window

Migration sırasında kaynak veri doğrudan değiştirilmemelidir.

---

# 72. SCHEMA EVOLUTION

Schema değişiklikleri aşağıdaki kurallara uymalıdır.

• Geriye dönük uyumluluk korunmalıdır.

• Yeni alanlar mümkün olduğunda Optional olmalıdır.

• Alan anlamı sessizce değiştirilemez.

• Kaldırılan alanlar önce Deprecated olmalıdır.

• Migration Script versiyonlanmalıdır.

• Rollback planı bulunmalıdır.

---

# 73. CACHE GOVERNANCE

Cache resmi veri kaynağı değildir.

Cache;

• yeniden üretilebilir olmalıdır,

• süreli olmalıdır,

• kaynak veriden türetilmelidir,

• veri kaybında sistemi bozmamalıdır.

Cache ile kalıcı veri birbirine karıştırılamaz.

---

# 74. TEMPORARY DATA

Temporary Data yalnızca Execution süresince kullanılabilir.

Örnek:

• Intermediate Results

• Temporary Files

• Runtime Cache

• Worker State

• Session Data

Execution tamamlandığında geçici veriler temizlenmelidir.

Kalıcı bilgi Temporary Store içerisinde saklanamaz.

---

# 75. DATA OBSERVABILITY

Platform aşağıdaki veri operasyonlarını izlemelidir.

• Data Creation

• Data Validation

• Data Versioning

• Data Access

• Data Migration

• Data Archive

• Data Deletion

• Data Recovery

Kritik veri operasyonları Audit kaydı üretmelidir.

---

# 76. DATA GOVERNANCE PRINCIPLES

### DATA-031

Her veri nesnesinin tek bir resmi sahibi olmalıdır.

---

### DATA-032

Immutable veri doğrudan değiştirilemez.

---

### DATA-033

Her türetilmiş veri kaynağına geri izlenebilmelidir.

---

### DATA-034

Company izolasyonu tüm veri katmanlarında korunmalıdır.

---

### DATA-035

Cache resmi veri kaynağı değildir.

---

### DATA-036

Schema değişiklikleri versiyonlanmalıdır.

---

### DATA-037

Migration işlemleri doğrulanabilir ve geri alınabilir olmalıdır.

---

### DATA-038

Veri kalitesi karar güvenini etkileyebilir.

---

### DATA-039

Audit kayıtları değiştirilemez.

---

### DATA-040

Fiziksel depolama teknolojisi mantıksal veri mimarisini değiştiremez.

---

# OFFICIAL DATA GOVERNANCE FLOW

Data Creation

↓

Classification

↓

Ownership Assignment

↓

Validation

↓

Versioning

↓

Storage

↓

Access Control

↓

Monitoring

↓

Archive / Retention

↓

Recovery / Retirement

---

# PART 06 COMPLETION STATUS

| Item                       | Status     |
| -------------------------- | ---------- |
| Data Ownership             | ✅ Complete |
| Data Versioning            | ✅ Complete |
| Retention Management       | ✅ Complete |
| Data Integrity             | ✅ Complete |
| Data Lineage               | ✅ Complete |
| Artifact Lineage Extension | ✅ Complete |
| Decision Graph Extension   | ✅ Complete |
| Data Security              | ✅ Complete |
| Backup & Recovery          | ✅ Complete |
| Data Migration             | ✅ Complete |
| Schema Evolution           | ✅ Complete |
| Data Governance Principles | ✅ Complete |

---

**DOCUMENT 06 — PART 06 COMPLETE**

# PART 07 — DATA ARCHITECTURE GOVERNANCE & ARCHITECTURAL COMPLIANCE

---

# 77. PURPOSE

Bu bölüm;

Stokonomi Data Architecture'ın

uzun vadeli sürdürülebilirliğini,

tutarlılığını,

güvenilirliğini,

ve genişletilebilirliğini güvence altına alır.

Veri mimarisi ile ilgili tüm geliştirmeler bu bölümde tanımlanan kurallara uymak zorundadır.

---

# 78. DATA ARCHITECTURAL INVARIANTS

Aşağıdaki kurallar Data Architecture için değiştirilemez.

### DATA-041

Operational Data sistemin tek resmi giriş verisidir.

---

### DATA-042

Execution Data yalnızca Execution Engine tarafından oluşturulur.

---

### DATA-043

Knowledge Data yalnızca AI Intelligence tarafından oluşturulur.

---

### DATA-044

Company Memory yalnızca ilgili şirkete aittir.

---

### DATA-045

Pattern Memory yalnızca ilgili SKU davranışını temsil eder.

---

### DATA-046

Artifact yalnızca tamamlanmış Decision sonucundan üretilebilir.

---

### DATA-047

Metadata iş verisinin yerine geçemez.

---

### DATA-048

Audit kayıtları değiştirilemez.

---

# 79. FORBIDDEN OPERATIONS

Aşağıdaki işlemler mimari ihlal olarak değerlendirilir.

• Operational Data'nın doğrudan değiştirilmesi

• AI'nın Company Memory'yi manuel güncellemesi

• Pattern Memory'nin kullanıcı tarafından düzenlenmesi

• Execution Result üzerinde sonradan değişiklik yapılması

• Decision Memory'nin silinmesi

• Feature Store'un Operational Data olarak kullanılması

• Cache'in resmi veri kaynağı kabul edilmesi

• Artifact'in kaynak veriden bağımsız oluşturulması

---

# 80. DATA EXTENSION RULES

Yeni veri bileşeni eklenirken aşağıdaki kurallar uygulanmalıdır.

Yeni veri modeli;

• Tek sorumluluğa sahip olmalıdır.

• Bir resmi Owner tanımlamalıdır.

• Version desteklemelidir.

• Audit üretmelidir.

• Metadata içermelidir.

• Trace edilebilir olmalıdır.

• Retention Policy tanımlamalıdır.

• Data Classification belirlemelidir.

---

# 81. COMPATIBILITY RULES

Yeni sürümler aşağıdaki yapıları bozamaz.

• Dataset Contract

• Execution Result Contract

• Company Memory Model

• Pattern Memory Model

• Decision Contract

• Artifact Contract

• Metadata Model

Kırıcı değişiklikler yalnızca yeni Major Version ile yapılabilir.

---

# 82. STORAGE INDEPENDENCE

Logical Data Architecture;

fiziksel depolama teknolojilerinden bağımsızdır.

Aşağıdaki teknolojiler değişebilir.

• PostgreSQL

• Redis

• Object Storage

• Vector Database

• Graph Database

• Search Index

Teknoloji değişimi veri mimarisini değiştirmez.

---

# 83. DATA OBSERVABILITY

Data Architecture aşağıdaki operasyonları izleyebilmelidir.

• Dataset Import

• Execution Creation

• Knowledge Update

• Decision Creation

• Artifact Generation

• Version Change

• Migration

• Archive

• Recovery

Kritik işlemler Monitoring ve Audit sistemine bildirilmelidir.

---

# 84. IMPLEMENTATION ORDER

Data Architecture aşağıdaki sırayla uygulanmalıdır.

Operational Data

↓

Execution Data

↓

Knowledge Data

↓

Memory Store

↓

Feature Store

↓

Artifact Store

↓

Metadata Store

↓

Governance

Bu sıra değiştirilmemelidir.

---

# 85. VALIDATION CHECKLIST

Yeni veri modeli eklenmeden önce aşağıdaki sorular cevaplanmalıdır.

□ Veri sahibi belli mi?

□ Veri sınıflandırıldı mı?

□ Version desteği var mı?

□ Metadata tanımlandı mı?

□ Trace edilebilir mi?

□ Audit üretiyor mu?

□ Retention tanımlandı mı?

□ Company izolasyonu korunuyor mu?

□ Architecture kurallarına uygun mu?

---

# 86. DOCUMENT DEPENDENCIES

Data Architecture aşağıdaki dokümanlara bağlıdır.

Document 01 — Foundation

↓

Document 02 — Domain Model

↓

Document 03 — Workflow Architecture

↓

Document 04 — Execution Engine

↓

Document 05 — AI Intelligence Architecture

↓

Document 06 — Data Architecture

Sonraki dokümanlar.

↓

Document 07 — Application Architecture

↓

Infrastructure

---

# 87. ARCHITECTURE COMPLIANCE

Platform içerisindeki tüm veri modelleri;

Document 01,

Document 02,

Document 03,

Document 04,

Document 05,

ve

Document 06

ile tam uyumlu olmak zorundadır.

Hiçbir implementasyon bu mimari ile çelişemez.

---

# 88. ARCHITECTURE FREEZE

Bu doküman;

Stokonomi Platformu'nun resmi Data Architecture referansıdır.

Data Architecture ile ilgili tüm geliştirmeler bu doküman referans alınarak yapılacaktır.

Bu mimari;

Architecture Decision Record (ADR) oluşturulmadan değiştirilemez.

---

# PART 07 COMPLETION STATUS

| Item                     | Status     |
| ------------------------ | ---------- |
| Architectural Invariants | ✅ Complete |
| Forbidden Operations     | ✅ Complete |
| Extension Rules          | ✅ Complete |
| Compatibility Rules      | ✅ Complete |
| Storage Independence     | ✅ Complete |
| Validation Checklist     | ✅ Complete |
| Architecture Freeze      | ✅ Complete |

---

# DOCUMENT 06 COMPLETION STATUS

| Part                                                              | Status     |
| ----------------------------------------------------------------- | ---------- |
| Part 01 — Data Architecture Foundation                            | ✅ Complete |
| Part 02 — Operational Data Model                                  | ✅ Complete |
| Part 03 — Intelligence Data Model                                 | ✅ Complete |
| Part 04 — Feature Store & Semantic Knowledge                      | ✅ Complete |
| Part 05 — Artifact Store & Metadata Architecture                  | ✅ Complete |
| Part 06 — Data Governance, Integrity & Lifecycle Management       | ✅ Complete |
| Part 07 — Data Architecture Governance & Architectural Compliance | ✅ Complete |

---

# DOCUMENT 06 STATUS

Architecture Freeze Candidate

Version: 2.0

Status: Complete

Next Document:

DOCUMENT_07_APPLICATION_ARCHITECTURE.md

# Revision — Product Architecture Phase 1

- **Revision date:** 2026-08-06
- **Revision status:** BINDING
- **ADR reference:** ADR-020

Data enrichment model:

Minimum required data → Basic Standalone Analysis.

Additional operational data → Richer Business Workflow output.

Supplier data → Supplier Allocation enrichment.

ERP/API feedback → Company Learning.

External Intelligence → Company Learning → Pattern Intelligence → AI Parameter Optimizer → Deterministic Analysis.

Optional-data absence must not block unrelated valid capabilities. Missing data must explicitly describe unavailable outputs; data availability automatically enables its corresponding capabilities. External data does not directly overwrite deterministic results. Learning feedback must be traceable and versioned, and company data remains isolated.
