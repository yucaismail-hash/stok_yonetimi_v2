"""Application-owned translation from technical codes to user notices."""

from typing import Optional

from app.application.errors.execution_notices import UserExecutionNotice


def map_execution_error_to_notice(code: str, retryable: bool, *, support_reference: Optional[str] = None, completed_work_preserved: bool = False) -> UserExecutionNotice:
    reference = support_reference or code
    common = {"completed_work_preserved": completed_work_preserved, "support_reference": reference, "severity": "error"}
    if code in {"EXECUTOR_NOT_CONFIGURED", "IMPLEMENTATION_NOT_FOUND"}:
        return UserExecutionNotice("Analiz başlatılamadı", "Sistem şu anda analizi başlatamadı.", "Şu anda bir işlem yapmanız gerekmiyor.", "İşlem kaydedildi ve teknik ekip tarafından incelenebilir.", "support_review_required", notice_code="analysis_start_failed", **common)
    if code in {"CAPABILITY_INPUT_INVALID", "DATASET_INPUT_INVALID"}:
        return UserExecutionNotice("Analiz için gerekli veriler eksik veya geçersiz", "Analizin çalışabilmesi için gerekli bazı bilgiler uygun değil.", "Belirtilen alanları kontrol ederek analizi yeniden başlatın.", "Sistem hatalı veya eksik alanları işaretler.", "manual_action_required", notice_code="analysis_input_invalid", **common)
    if code == "DATASET_INPUT_UNAVAILABLE" and retryable:
        return UserExecutionNotice("Verilere geçici olarak ulaşılamadı", "Analiz için gerekli verilere şu anda ulaşılamıyor.", "Şu anda bir işlem yapmanız gerekmiyor.", "Sistem işlemi daha sonra yeniden deneyebilir.", "automatic_retry_possible", notice_code="dataset_temporarily_unavailable", **common)
    if code == "CAPABILITY_TIMEOUT":
        return UserExecutionNotice("Analiz beklenenden uzun sürdü", "İşlem belirlenen süre içinde tamamlanamadı.", "Şu anda bir işlem yapmanız gerekmiyor.", "Sistem uygun olduğunda işlemi otomatik olarak yeniden deneyebilir.", "automatic_retry_possible", notice_code="analysis_duration_exceeded", **common)
    if code == "INVALID_CAPABILITY_RESULT":
        return UserExecutionNotice("Analiz sonucu doğrulanamadı", "Hesaplama tamamlandı ancak oluşan sonuç güvenli biçimde kullanılamadı.", "Sistem yöneticisi veya destek ekibi incelemesi gerekebilir.", "Sonuç rapora, öğrenme sürecine veya karar sürecine dahil edilmez.", "support_review_required", notice_code="analysis_result_invalid", **common)
    retry_status = "automatic_retry_possible" if retryable else "support_review_required"
    user_action = "Şu anda bir işlem yapmanız gerekmiyor." if retryable else "Sistem yöneticisi veya destek ekibi incelemesi gerekebilir."
    system_action = "Sistem işlemi daha sonra yeniden deneyebilir." if retryable else "İşlem kaydedildi ve teknik ekip tarafından incelenebilir."
    return UserExecutionNotice("Analiz tamamlanamadı", "Hesaplama sırasında bir sorun oluştu.", user_action, system_action, retry_status, notice_code="analysis_execution_failed", **common)
