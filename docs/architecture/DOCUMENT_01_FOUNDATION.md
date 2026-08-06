STOKONOMI ARCHITECTURE SPECIFICATION v2.0
DOCUMENT 01
FOUNDATION & ARCHITECTURE PRINCIPLES

Version: 2.0
Status: Draft → Architecture Freeze Candidate
Priority: Mandatory
Scope: Entire Stokonomi Platform

1. PURPOSE

Bu doküman, Stokonomi platformunun resmi mimari temelini tanımlar.

Bu dokümanda belirtilen kurallar;

sistem mimarisi,
yazılım geliştirme,
AI karar mekanizması,
veri akışı,
modül ilişkileri,
gelecekte yapılacak tüm geliştirmeler

için bağlayıcıdır.

Hiçbir modül bu dokümanda tanımlanan mimari kuralları ihlal edemez.

2. ARCHITECTURAL VISION

Stokonomi klasik bir stok yönetim yazılımı değildir.

Stokonomi;

AI destekli karar verme platformudur.

Sistemin amacı;

stok hesaplamak değildir,
tahmin üretmek değildir,
rapor göstermek değildir.

Asıl amaç;

işletmenin en doğru operasyonel kararını üretmektir.

Bu nedenle;

Forecast,

Safety Stock,

Simulation,

Supplier,

Backtest,

Learning,

Decision Intelligence

bağımsız ürünler değildir.

Hepsi aynı karar sisteminin bileşenleridir.

3. CORE PHILOSOPHY

Platform aşağıdaki prensip üzerine kuruludur.

Every execution exists to improve decision quality.

Her çalıştırma;

bilgi üretir,
öğrenme oluşturur,
AI hafızasını geliştirir,
gelecekteki kararları iyileştirir.

Hiçbir analiz tek kullanımlık değildir.

4. SYSTEM MISSION

Platformun görevi;

ham veriyi,

işletmeye değer üreten

AI destekli kararlara dönüştürmektir.

Sistem hiçbir zaman yalnızca hesap makinesi olarak davranmaz.

Her çıktı;

yorumlanabilir,

açıklanabilir,

öğrenilebilir,

yeniden kullanılabilir

olmalıdır.

5. CORE PRINCIPLES

Platform aşağıdaki temel prensiplere uymak zorundadır.

P1

Business First

Teknik kararlar,

iş ihtiyacını desteklemek zorundadır.

P2

AI Assisted Decision Making

AI,

hesaplama motorunun yerine geçmez.

AI,

hesaplanan sonuçları yorumlar.

P3

Single Source of Truth

Her bilgi için yalnızca tek resmi kaynak bulunur.

Örnek;

Execution Status

tek bir modelden okunmalıdır.

P4

Layer Isolation

Katmanlar birbirlerinin sorumluluğunu üstlenemez.

P5

Deterministic Execution

Aynı giriş,

aynı parametre,

aynı veri,

aynı sonucu üretmelidir.

P6

Explainability

Üretilen her karar açıklanabilir olmak zorundadır.

P7

Learning Continuity

Her execution,

öğrenme sistemine katkı sağlamalıdır.

P8

Artifact Centric Architecture

Analiz sonuçları geçici değildir.

Kalıcı AI Artifact üretmek zorundadır.

6. OFFICIAL PLATFORM OBJECTIVE

Platformun tek amacı;

İşletmenin operasyonel karar kalitesini artırmaktır.

Bunun dışındaki tüm modüller bu amacı destekleyen alt sistemlerdir.

7. OFFICIAL EXECUTION FLOW

Platformun resmi işlem akışı aşağıdaki gibidir.

User Request
      │
      ▼
API Layer
      │
      ▼
Application Layer
      │
      ▼
Workflow Dispatcher
      │
      ▼
Workflow Engine
      │
      ▼
Execution Engine
      │
      ▼
Analytical Engines
      │
      ▼
Learning Engine
      │
      ▼
Decision Intelligence
      │
      ▼
AI Artifact
      │
      ▼
Persistence
      │
      ▼
Events
      │
      ▼
Integration

Bu akışın herhangi bir adımı atlanamaz.

8. OFFICIAL DESIGN GOALS

Platform aşağıdaki kalite hedeflerini sağlamalıdır:

Modülerlik
Genişletilebilirlik
Test edilebilirlik
Açıklanabilirlik
İzlenebilirlik (Traceability)
Tekrarlanabilirlik (Reproducibility)
Geriye dönük uyumluluk (Backward Compatibility)
AI destekli öğrenebilirlik

PART 02 — ARCHITECTURE GOVERNANCE & LAYER PRINCIPLES
9. ARCHITECTURE GOVERNANCE

Bu mimari, Stokonomi platformunun tek resmi mimarisidir.

Tüm yeni geliştirmeler, refactoring çalışmaları ve entegrasyonlar bu dokümanda tanımlanan kurallara uymak zorundadır.

Hiçbir geliştirici veya AI aracı bu kuralların dışına çıkarak mimari karar üretemez.

Bu doküman "Single Source of Truth" olarak kabul edilir.

10. LAYERED ARCHITECTURE

Platform aşağıdaki katmanlardan oluşur.

Presentation Layer
        │
        ▼
API Layer
        │
        ▼
Application Layer
        │
        ▼
Workflow Dispatcher
        │
        ▼
Workflow Engine
        │
        ▼
Execution Engine
        │
        ▼
Analytical Engines
        │
        ▼
Learning Engine
        │
        ▼
Decision Intelligence
        │
        ▼
AI Artifact Layer
        │
        ▼
Persistence Layer
        │
        ▼
Event Layer
        │
        ▼
Integration Layer

Bu sıralama platformun resmi yürütme sırasıdır.

11. RESPONSIBILITY PRINCIPLE

Her katmanın yalnızca bir temel sorumluluğu olabilir.

Katmanlar başka katmanların görevlerini üstlenemez.

Layer	Responsibility
Presentation	Kullanıcı deneyimi
API	Request / Response
Application	Use Case Orchestration
Workflow Dispatcher	İş akışını seçmek
Workflow Engine	Execution yönetimi
Execution Engine	Analitik motorları çalıştırmak
Analytical Engines	Hesaplama yapmak
Learning	Bilgi üretmek
Decision Intelligence	Karar üretmek
AI Artifact	Sonucu standartlaştırmak
Persistence	Kalıcı kayıt
Events	İş olaylarını yayınlamak
Integration	Dış sistem iletişimi
12. LAYER ISOLATION RULE

Hiçbir katman kendi üstündeki katmana bağımlı olamaz.

Doğru bağımlılık:

API
↓
Application
↓
Workflow

Yanlış bağımlılık:

Workflow
↓
API

Bu yapı kesinlikle yasaktır.

13. DEPENDENCY DIRECTION

Bağımlılıklar yalnızca aşağı doğru ilerleyebilir.

Presentation
↓

API
↓

Application
↓

Workflow
↓

Engine
↓

Repository
↓

Database

Yukarı yönlü bağımlılık oluşturulamaz.

14. FORBIDDEN DEPENDENCIES

Aşağıdaki bağımlılıklar kesin olarak yasaktır.

❌ API → Analytical Engine

❌ API → Learning Engine

❌ API → Decision Intelligence

❌ API → Repository

❌ Application → Database

❌ Decision Intelligence → API

❌ Learning → API

❌ Integration → Workflow Engine

❌ Event → Analytical Engine

❌ Repository → Workflow

15. CANONICAL COMPONENT PRINCIPLE

Platform içerisinde aynı sorumluluğu üstlenen yalnızca bir resmi bileşen bulunabilir.

Örneğin:

Canonical Workflow Engine

app/engine/workflow_engine.py

Canonical olmayan implementasyonlar:

geçici olabilir,
legacy olabilir,
migration sürecinde bulunabilir.

Ancak yeni geliştirmeler bunları kullanamaz.

16. SINGLE EXECUTION PATH

Resmi execution akışı yalnızca aşağıdaki yol üzerinden çalışabilir.

API
↓

Application

↓

Workflow Dispatcher

↓

Workflow Engine

↓

Execution Engine

↓

Analytical Engines

↓

Learning

↓

Decision Intelligence

↓

AI Artifact

Alternatif execution yolu oluşturulamaz.

17. NO BUSINESS LOGIC RULE

Aşağıdaki katmanlarda iş mantığı bulunamaz:

API
Integration
Events
Repository

Bu katmanlar yalnızca yönlendirme, iletişim ve veri taşıma görevini üstlenir.

18. APPLICATION LAYER PRINCIPLE

Application Layer;

hesaplama yapmaz,
AI çalıştırmaz,
veri analizi yapmaz.

Görevi yalnızca:

Use Case oluşturmak,
Workflow Dispatcher'a yönlendirmek,
sonucu geri döndürmektir.
19. WORKFLOW DISPATCHER PRINCIPLE

Workflow Dispatcher sistemin tek giriş kapısıdır.

Hiçbir bileşen Workflow Engine'i doğrudan çalıştıramaz.

İzin verilen akış:

Application

↓

Workflow Dispatcher

↓

Workflow Engine
20. EXTENSIBILITY PRINCIPLE

Yeni modül eklenirken mevcut modüller değiştirilmemelidir.

Yeni özellikler;

Plugin,
Strategy,
Adapter,
Provider,
Capability

mekanizmaları ile sisteme eklenmelidir.

PART 03 — DEPENDENCY RULES, PACKAGE STANDARDS & CANONICAL COMPONENTS
21. DEPENDENCY GOVERNANCE

Tüm bağımlılıklar (dependencies), platformun resmi mimari akışına uygun olmak zorundadır.

Hiçbir modül mimari katmanları atlayamaz.

Bağımlılıklar yalnızca aşağıdaki yönde ilerleyebilir.

Presentation
      ↓
API
      ↓
Application
      ↓
Workflow Dispatcher
      ↓
Workflow Engine
      ↓
Execution Engine
      ↓
Analytical Engines
      ↓
Learning
      ↓
Decision Intelligence
      ↓
AI Artifact
      ↓
Persistence
      ↓
Events
      ↓
Integration
22. OFFICIAL PACKAGE STRUCTURE

Platformun resmi paket organizasyonu aşağıdaki gibidir.

app/

api/
application/
engine/
analysis/
learning/
decision_intelligence/
services/
repositories/
models/
events/
integration/
clients/
security/
rate_limiter/
schemas/
utils/

Yeni paketler yalnızca mimari gerektiriyorsa eklenebilir.

23. PACKAGE RESPONSIBILITY

Her paket yalnızca tek bir sorumluluğa sahip olabilir.

Package	Responsibility
api	HTTP Communication
application	Use Case Coordination
engine	Workflow Execution
analysis	Analytical Algorithms
learning	Knowledge Production
decision_intelligence	Decision Generation
services	Domain Services
repositories	Persistence Access
models	Domain Models
events	Business Events
integration	External Systems
security	Authentication & Authorization
clients	SDK
schemas	API Contracts
utils	Generic Utilities
24. CANONICAL COMPONENTS

Platformun resmi implementasyonları aşağıdaki tablodur.

Responsibility	Official Component
Workflow Engine	app/engine/workflow_engine.py
Execution Context	app/engine/execution_context.py
Orchestrator	app/engine/orchestrator.py
Learning Engine	app/learning/learning_engine.py
Decision Intelligence	app/decision_intelligence/decision_intelligence_engine.py
Execution Service	app/services/execution/execution_service.py
Repository Layer	app/repositories/*

Bu liste Architecture Decision Log ile yönetilir.

25. TRANSITION COMPONENTS

Migration sürecinde bazı bileşenler sistemde bulunabilir.

Bunlar çalışıyor olabilir.

Ancak yeni geliştirmeler bunları referans alamaz.

Örnekler:

app/engine/execution_service.py

app/orchestration/*

Bu bileşenler;

Operational olabilir.
Legacy olabilir.
Experimental olabilir.

Ancak Canonical değildir.

26. ARCHITECTURAL DECISION RECORD (ADR)

Her önemli mimari karar kayıt altına alınmalıdır.

Örnek:

ADR-001

Official Workflow Engine

Component

app/engine/workflow_engine.py

Status

Accepted

Reason

Single execution path
27. NAMING CONVENTION

İsimlendirme aşağıdaki standartlara uymalıdır.

Package
snake_case

Örnek

decision_intelligence
Module
snake_case.py

Örnek

workflow_engine.py
Class
PascalCase

Örnek

WorkflowEngine
Function
snake_case()

Örnek

execute_workflow()
Constants
UPPER_CASE

Örnek

DEFAULT_TIMEOUT
28. IMPORT STANDARDS

Import kuralları aşağıdaki sıraya göre yapılmalıdır.

# Standard Library

import logging

from uuid import UUID

# Third Party

from fastapi import APIRouter

# Internal

from app.application...

from app.engine...

from app.repositories...

Wildcard import yasaktır.

from module import *

Relative import yalnızca aynı paket içerisinde kullanılabilir.

29. PUBLIC API RULE

Her paket yalnızca public API'sini dışarı açmalıdır.

Internal implementasyonlar doğrudan kullanılmamalıdır.

Örnek

Doğru

from app.services.execution import ExecutionService

Yanlış

from app.services.execution.execution_service import InternalExecutionState

Public API, gerektiğinde __init__.py üzerinden tanımlanmalıdır. Ancak __init__.py yalnızca gerçek bir public API ihtiyacı varsa kullanılmalıdır; sadece "her klasörde bulunsun" amacıyla oluşturulmaz.

30. FORBIDDEN STRUCTURES

Aşağıdaki yapılar yasaktır.

❌ Aynı sorumluluğu taşıyan iki Canonical Component

❌ API içerisinde Business Logic

❌ Repository içerisinde AI hesaplaması

❌ Engine içerisinde HTTP işlemleri

❌ Learning içerisinde SQL sorguları

❌ Decision Intelligence içerisinde Repository yönetimi

❌ Integration içerisinde Workflow çalıştırılması

31. ARCHITECTURAL EXCEPTIONS

Geçici istisnalar yalnızca migration süresince kabul edilir.

İstisnalar:

Decision Log'a yazılmalıdır.
Gerekçesi belirtilmelidir.
Kaldırılacağı faz tanımlanmalıdır.

Örnek:

Exception ID

EX-003

Reason

Legacy Execution Service

Removal Phase

Phase 8

Status

Temporary
32. ARCHITECTURE COMPLIANCE

Yeni eklenen her modül aşağıdaki sorulara "Evet" cevabı verebilmelidir.

Doğru katmanda mı?
Canonical bileşeni mi kullanıyor?
Yasak bağımlılık oluşturuyor mu?
Public API kurallarına uyuyor mu?
Single Execution Path'i koruyor mu?
Decision Log gerektiriyor mu?

Bu sorulardan herhangi birine "Hayır" cevabı veriliyorsa değişiklik mimari incelemeye alınmalıdır.

PART 04 — ARCHITECTURE GOVERNANCE, QUALITY ATTRIBUTES & DESIGN CONSTRAINTS
33. ARCHITECTURE GOVERNANCE MODEL

Platform mimarisi aşağıdaki yönetim modeli ile korunur.

Architecture Specification
        │
        ▼
Architecture Decision Records (ADR)
        │
        ▼
Coding Standards
        │
        ▼
Repository
        │
        ▼
CI Validation

Hiçbir kod, Architecture Specification'ın önüne geçemez.

34. SINGLE SOURCE OF TRUTH

Her mimari kararın yalnızca tek resmi kaynağı vardır.

Artifact	Official Source
Architecture Rules	Architecture Specification
Component Status	ADR
Migration Status	Migration Log
API Contract	API Documentation
Domain Rules	Domain Documents

Birden fazla resmi kaynak oluşturulamaz.

35. QUALITY ATTRIBUTES

Platform aşağıdaki kalite hedeflerini korumak zorundadır.

Maintainability

Kod okunabilir ve sürdürülebilir olmalıdır.

Extensibility

Yeni modüller mevcut kod değiştirilmeden eklenebilmelidir.

Scalability

İş yükü arttığında sistem yatay ve dikey ölçeklenebilmelidir.

Reliability

Beklenmeyen durumlarda sistem kontrollü şekilde çalışmaya devam etmelidir.

Observability

Her execution;

izlenebilir,
loglanabilir,
denetlenebilir olmalıdır.
Testability

Her katman bağımsız test edilebilir olmalıdır.

Explainability

AI tarafından üretilen her karar açıklanabilir olmalıdır.

36. DESIGN CONSTRAINTS

Aşağıdaki tasarım kısıtları zorunludur.

C1

Business Logic yalnızca uygun katmanda bulunabilir.

C2

Her modül tek sorumluluk ilkesine uymalıdır.

C3

Hiçbir modül kendi kendisini çalıştıramaz.

Execution yalnızca Workflow üzerinden başlatılır.

C4

Hiçbir AI modülü doğrudan kullanıcı isteği alamaz.

C5

Repository yalnızca veri erişim katmanıdır.

C6

Integration katmanı yalnızca dış sistem iletişiminden sorumludur.

37. FAIL SAFE PRINCIPLE

Platform hata durumlarında tamamen durmak yerine kontrollü şekilde çalışmaya devam etmelidir.

Örnekler:

Forecast başarısız olursa diğer analizler devam edebilir.
Explainability üretilemezse Artifact yine oluşturulabilir.
Opsiyonel AI zenginleştirmeleri başarısız olsa bile temel analiz tamamlanmalıdır.

Bu ilke, önceki tasarım kararlarımızla uyumludur: zorunlu bağımlılıklar ile zenginleştirme (enrichment) bağımlılıkları birbirinden ayrılır.

38. BACKWARD COMPATIBILITY

Mimari değişiklikler mevcut çalışan sistemi gereksiz yere bozmaz.

Kurallar:

Public API korunur.
Migration planı tanımlanır.
Legacy bileşenler kontrollü kaldırılır.
Ani kırılmalar (breaking changes) yapılmaz.
39. ARCHITECTURAL EVOLUTION

Platform yaşayan bir mimaridir.

Yeni modüller eklenebilir.

Yeni AI modelleri eklenebilir.

Yeni entegrasyonlar eklenebilir.

Ancak aşağıdaki ilkeler değiştirilemez:

Layered Architecture
Single Execution Path
Canonical Components
AI Artifact Architecture
Event Driven Architecture
40. DEPRECATION POLICY

Bir bileşen kaldırılmadan önce aşağıdaki süreç izlenir.

Experimental
      │
      ▼
Supported
      │
      ▼
Deprecated
      │
      ▼
Legacy
      │
      ▼
Removed

Hiçbir Canonical Component doğrudan silinemez.

41. MIGRATION PRINCIPLES

Migration aşağıdaki prensiplere göre yürütülür.

Incremental Replacement
Feature Freeze
Backward Compatibility
Architecture First
Repository Second

Yani:

Önce mimari tanımlanır, sonra kod mimariye uyarlanır.

42. AI GOVERNANCE

Platformdaki AI aşağıdaki kurallara uymalıdır.

AI;

karar destek mekanizmasıdır.
deterministik hesaplamaların yerine geçmez.
analitik motorları değiştirmez.
hesaplanan sonuçları yorumlar.
açıklama üretir.
öneri sunar.

AI hiçbir zaman gizli iş mantığı üretmemelidir.

43. ARCHITECTURE REVIEW PROCESS

Her büyük değişiklik aşağıdaki süreçten geçer.

Proposal
      │
      ▼
Architecture Review
      │
      ▼
ADR
      │
      ▼
Implementation
      │
      ▼
Validation
      │
      ▼
Architecture Freeze
44. COMPLIANCE REQUIREMENTS

Yeni geliştirilen her bileşen aşağıdaki kontrol listesini geçmelidir.

Doğru katmanda mı?
Mimari bağımlılık kurallarına uyuyor mu?
Canonical bileşenleri kullanıyor mu?
Public API kurallarını ihlal ediyor mu?
AI Artifact mimarisine uyuyor mu?
Event mimarisine uyuyor mu?
Integration kurallarını ihlal ediyor mu?
ADR gerektiriyor mu?

Bu kontroller sağlanmadan kod üretime alınamaz.

PART 05 — TERMINOLOGY, ARCHITECTURE DICTIONARY & GOVERNANCE APPENDIX
45. OFFICIAL TERMINOLOGY

Bu bölümde tanımlanan terimler Stokonomi platformunun resmi terminolojisidir.

Hiçbir doküman veya kod bu terimleri farklı anlamlarda kullanamaz.

AI Artifact

Analitik süreç sonunda üretilen standartlaştırılmış ve kalıcı karar çıktısıdır.

AI Artifact;

versiyonlanabilir,
açıklanabilir,
yeniden kullanılabilir,
paylaşılabilir

olmalıdır.

Analysis Engine

Belirli bir analitik problemi çözen hesaplama motorudur.

Örnekler:

Forecast
Safety Stock
Simulation
Supplier
Backtest
Application Layer

Use-case koordinasyon katmanıdır.

İş mantığı çalıştırmaz.

Workflow Dispatcher'a yönlendirme yapar.

Canonical Component

Belirli bir sorumluluğun resmi implementasyonudur.

Yeni geliştirmeler yalnızca Canonical Component'leri kullanmalıdır.

Decision Intelligence

Analitik sonuçları işletme kararına dönüştüren AI katmanıdır.

Event

İş süreçlerinde meydana gelen değiştirilemez (immutable) iş olayıdır.

Örnek:

DatasetUploaded
ExecutionCompleted
ArtifactPublished
Execution

Bir iş hedefini gerçekleştirmek amacıyla başlatılan çalışma sürecidir.

Execution Context

Execution boyunca taşınan ortak çalışma bağlamıdır.

Integration Adapter

Dış sistemlerle platform arasındaki çeviri katmanıdır.

İş mantığı içermez.

Learning Engine

Execution sonuçlarından bilgi üreten öğrenme katmanıdır.

Workflow

Belirli bir iş hedefini gerçekleştirmek için yürütülen adımlar dizisidir.

Workflow Dispatcher

Execution'ın hangi Workflow tarafından yürütüleceğine karar veren bileşendir.

Workflow Engine

Workflow'u yöneten ana yürütme motorudur.

46. COMPONENT STATUS DEFINITIONS

Her bileşen aşağıdaki durumlardan yalnızca birine sahip olabilir.

Status	Description
Experimental	Deneme aşamasında
Candidate	Değerlendiriliyor
Canonical	Resmi implementasyon
Deprecated	Kullanımı bırakılıyor
Legacy	Sadece uyumluluk amacıyla korunuyor
Removed	Sistemden kaldırıldı
47. ARCHITECTURE DECISION RECORD (ADR) TEMPLATE

Her mimari karar aşağıdaki formatta kayıt altına alınmalıdır.

ADR ID

Title

Status

Context

Decision

Alternatives Considered

Consequences

Migration Impact

Approved By

Date
Örnek
ADR-001

Official Workflow Engine

Status

Accepted

Decision

app/engine/workflow_engine.py

Reason

Single execution path

Migration

Legacy WorkflowEngine retained until Phase 8
48. DESIGN REVIEW CHECKLIST

Her yeni geliştirme aşağıdaki sorularla değerlendirilmelidir.

Mimari
Doğru katmanda mı?
Single Responsibility ilkesine uyuyor mu?
Canonical Component kullanıyor mu?
Bağımlılık
Yasak dependency oluşturuyor mu?
Döngüsel bağımlılık oluşturuyor mu?
Kalite
Test edilebilir mi?
İzlenebilir mi?
Açıklanabilir mi?
AI
AI yalnızca yorum mu yapıyor?
Deterministik hesaplamaları değiştirmiyor mu?
Entegrasyon
Integration Adapter üzerinden mi çalışıyor?
Event üretmesi gerekiyor mu?
49. DOCUMENT HIERARCHY

Architecture Specification aşağıdaki sırayla okunmalıdır.

Architecture Index
        │
        ▼
Document 01
        │
        ▼
Document 02
        │
        ▼
Document 03
        │
        ▼
Document 04
        │
        ▼
Document 05
        │
        ▼
Document 06
        │
        ▼
Document 07

Hiçbir Document önceki dokümanlarla çelişemez.

50. ARCHITECTURE FREEZE

Document 01 onaylandıktan sonra aşağıdaki konular dondurulur (Architecture Freeze).

Mimari katmanlar
Bağımlılık yönü
Canonical Component tanımları
Terminoloji
İsimlendirme standartları
Governance modeli

Bu konularda değişiklik yapılması yalnızca yeni bir ADR ile mümkündür.

DOCUMENT 01 COMPLETION CRITERIA

Document 01 aşağıdaki hedefleri karşılar:

Platformun vizyonunu tanımlar.
Mimari katmanları tanımlar.
Katman sorumluluklarını belirler.
Bağımlılık kurallarını tanımlar.
Canonical bileşenleri tanımlar.
İsimlendirme standartlarını belirler.
Mimari yönetişim (governance) modelini oluşturur.
Ortak terminolojiyi standartlaştırır.
ADR sürecini tanımlar.
Sonraki tüm dokümanlar için temel referans olur.
DOCUMENT 01 STATUS
Item	Status
Foundation	✅ Complete
Architecture Principles	✅ Complete
Layer Rules	✅ Complete
Dependency Rules	✅ Complete
Canonical Components	✅ Complete
Naming Standards	✅ Complete
Governance	✅ Complete
Terminology	✅ Complete
ADR Standard	✅ Complete
Architecture Freeze Ready	✅ Yes
DOCUMENT 01 — ARCHITECTURE FOUNDATION

Status: Architecture Freeze Candidate

# Revision — Product Architecture Phase 1

- **Revision date:** 2026-08-06
- **Revision status:** BINDING
- **ADR reference:** ADR-020

Stokonomi has two user-visible product levels. Level 1, Standalone Analysis, runs one selected analytical capability and returns an analysis-level AI Explanation Artifact. Level 2, Business Workflow, orchestrates ordered capabilities and returns a Dynamic Operational Plan followed by a final AI Artifact.

Standalone Analysis and Business Workflow are distinct execution-intent domains. Deterministic engines remain the calculation authority; AI learns, optimizes parameters, supports decisions, and explains results without replacing deterministic calculation.

Level 1 flow: API → Application → WorkflowDispatcher → Single Analysis Workflow → Selected Capability → Learning → AI Explanation Artifact.

Level 2 flow: API → Application → WorkflowDispatcher → Business Objective Workflow → Ordered Capabilities → Learning → Decision Intelligence → Dynamic Operational Plan → AI Artifact.

