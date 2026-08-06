# app/decision_intelligence/decision_intelligence_engine.py
"""
Decision Intelligence Engine - DOCUMENT 06 - PART 01
Main orchestrator for Decision Intelligence & Communication.

DOCUMENT 06A Integration:
- Every communication output SHALL become an AI Artifact
- AI Artifacts SHALL be created through ArtifactFactory
- AI Artifacts SHALL be persisted through ArtifactPersistenceService
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from uuid import UUID

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.narrative_generator import NarrativeGenerator
from app.decision_intelligence.narrative_persistence import NarrativePersistence
from app.decision_intelligence.narrative_validator import NarrativeValidator

# DOCUMENT 06A - AI Artifact imports
from app.services.artifact.artifact_factory import ArtifactFactory
from app.services.artifact.artifact_persistence_service import ArtifactPersistenceService
from app.services.artifact.artifact_explainability import ArtifactExplainability
from app.repositories.artifact_repository import ArtifactRepository
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class DecisionIntelligenceEngine:
    """
    Decision Intelligence Engine - DOCUMENT 06
    
    Main orchestrator for Decision Intelligence & Communication.
    
    DOCUMENT 06A Integration:
    - Every narrative output becomes an AI Artifact
    - Artifacts are created through ArtifactFactory
    - Artifacts are persisted through ArtifactPersistenceService
    """
    
    def __init__(self):
        self.narrative_generator = NarrativeGenerator()
        self.narrative_persistence = NarrativePersistence()
        self.narrative_validator = NarrativeValidator()
        
        # DOCUMENT 06A - Artifact components
        self.artifact_factory = ArtifactFactory()
        self.artifact_explainability = ArtifactExplainability()
    
    def process(
        self,
        context: DecisionContext,
        force_regeneration: bool = False,
    ) -> Dict[str, Any]:
        """
        Process decision intelligence pipeline.
        
        Args:
            context: DecisionContext with all results
            force_regeneration: Force regeneration of narrative
        
        Returns:
            Complete decision intelligence result with AI Artifact
        """
        logger.info(f"🧠 Decision Intelligence started: {context.execution_id}")
        
        # 1. Check if narrative exists (reuse policy - DOCUMENT 06A)
        if not force_regeneration:
            existing = self.narrative_persistence.get_by_execution(str(context.execution_id))
            if existing:
                logger.info(f"✅ Using existing narrative for execution: {context.execution_id}")
                
                # DOCUMENT 06A: Check if artifact exists for reuse
                artifact = self._get_artifact_by_execution(context.execution_id)
                
                return {
                    "status": "reused",
                    "narrative": existing,
                    "artifact": artifact,
                    "metadata": {
                        "execution_id": str(context.execution_id),
                        "reused": True,
                        "timestamp": context.generated_at.isoformat(),
                    },
                }
        
        # 2. Generate narrative
        narrative = self.narrative_generator.generate(context, force_regeneration)
        
        # 3. Validate narrative
        is_valid, errors = self.narrative_validator.validate(narrative, context)
        
        if not is_valid:
            logger.warning(f"⚠️ Narrative validation failed: {errors}")
            narrative["_validation_errors"] = errors
            narrative["_is_valid"] = False
        else:
            narrative["_is_valid"] = True
        
        # 4. DOCUMENT 06A: Create AI Artifact
        artifact = self._create_artifact_from_narrative(
            context=context,
            narrative=narrative,
            is_valid=is_valid,
            errors=errors
        )
        
        # 5. Prepare result
        result = {
            "status": "generated" if not force_regeneration else "regenerated",
            "narrative": narrative,
            "artifact": artifact,
            "validation": {
                "is_valid": is_valid,
                "errors": errors,
            },
            "metadata": {
                "execution_id": str(context.execution_id),
                "workflow_id": context.workflow_id,
                "business_objective": context.business_objective,
                "generated_at": context.generated_at.isoformat(),
                "prompt_version": context.prompt_version,
                "narrative_version": context.narrative_version,
                "artifact_id": str(artifact.get("id")) if artifact else None,
                "artifact_version": artifact.get("artifact_version") if artifact else None,
            },
        }
        
        if force_regeneration:
            result["status"] = "regenerated"
            result["metadata"]["regenerated_at"] = datetime.now().isoformat()
        
        logger.info(f"✅ Decision Intelligence completed: {context.execution_id}")
        
        return result
    
    def regenerate(
        self,
        context: DecisionContext,
    ) -> Dict[str, Any]:
        """
        Regenerate narrative for existing context.
        """
        return self.process(context, force_regeneration=True)
    
    def get_narrative(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get narrative by execution ID.
        """
        return self.narrative_persistence.get_by_execution(execution_id)
    
    def get_narrative_by_id(self, narrative_id: str) -> Optional[Dict[str, Any]]:
        """
        Get narrative by narrative ID.
        """
        return self.narrative_persistence.get_narrative(narrative_id)
    
    def list_narratives(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all narratives.
        """
        return self.narrative_persistence.list_narratives(limit)
    
    def validate_narrative(self, narrative: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """
        Validate a narrative independently.
        """
        is_valid, errors = self.narrative_validator.validate(narrative, context)
        return {
            "is_valid": is_valid,
            "errors": errors,
        }
    
    # ====================================================================
    # DOCUMENT 06A - AI Artifact Methods
    # ====================================================================
    
    def _get_artifact_by_execution(self, execution_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get AI Artifact by execution ID.
        
        DOCUMENT 06A: Reuse Policy - Previously generated AI Artifacts
        SHALL always be reused.
        """
        try:
            db = SessionLocal()
            repository = ArtifactRepository(db)
            artifact = repository.get_by_execution(execution_id)
            
            if artifact:
                return {
                    "id": str(artifact.id),
                    "artifact_type": artifact.artifact_type,
                    "artifact_version": artifact.artifact_version,
                    "status": artifact.status,
                    "is_reused": artifact.is_reused,
                    "reuse_count": artifact.reuse_count,
                    "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting artifact by execution: {e}")
            return None
        finally:
            db.close()
    
    def _create_artifact_from_narrative(
        self,
        context: DecisionContext,
        narrative: Dict[str, Any],
        is_valid: bool,
        errors: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Create AI Artifact from narrative output.
        
        DOCUMENT 06A:
        - Every communication output SHALL become an AI Artifact
        - AI Artifacts SHALL be created through ArtifactFactory
        - AI Artifacts SHALL be persisted through ArtifactPersistenceService
        """
        try:
            # 1. Build content structure for artifact
            content = self._build_artifact_content(context, narrative, is_valid, errors)
            
            # 2. Build explainability
            explainability = self.artifact_explainability.build_explainability(
                source="Decision Intelligence Engine - Narrative Generator",
                generation_time=context.generated_at,
                contributing_modules=[
                    "NarrativeGenerator",
                    "NarrativeValidator",
                    "DecisionContext"
                ],
                supporting_evidence=[
                    {
                        "type": "execution_id",
                        "value": str(context.execution_id)
                    },
                    {
                        "type": "workflow_id",
                        "value": context.workflow_id
                    },
                    {
                        "type": "business_objective",
                        "value": context.business_objective
                    },
                    {
                        "type": "has_results",
                        "value": bool(context.results)
                    }
                ]
            )
            
            # 3. Add explainability to content
            content["explainability"] = explainability
            
            # 4. Create artifact through factory
            artifact = self.artifact_factory.create_analysis_narrative(
                company_id=context.company_id,
                execution_id=context.execution_id,
                dataset_id=context.dataset_id,
                content=content,
                generated_by=context.user_id,
                metadata={
                    "language": context.language or "tr",
                    "prompt_version": context.prompt_version or "1.0",
                    "schema_version": "1.0",
                    "communication_contract_version": "1.0",
                    "artifact_version": 1,
                    "llm_provider": context.llm_provider,
                    "llm_model": context.llm_model,
                    "model_version": context.model_version,
                }
            )
            
            # 5. Persist artifact
            db = SessionLocal()
            repository = ArtifactRepository(db)
            persistence_service = ArtifactPersistenceService(repository)
            
            persisted_artifact = persistence_service.persist(artifact)
            
            # 6. If validation passed, publish the artifact
            if is_valid:
                persisted_artifact = persistence_service.publish(
                    artifact_id=persisted_artifact.id,
                    published_by=context.user_id
                )
            
            # 7. Return artifact summary
            return {
                "id": str(persisted_artifact.id),
                "artifact_type": persisted_artifact.artifact_type,
                "artifact_subtype": persisted_artifact.artifact_subtype,
                "artifact_version": persisted_artifact.artifact_version,
                "status": persisted_artifact.status,
                "validation_status": persisted_artifact.validation_status,
                "is_reused": persisted_artifact.is_reused,
                "reuse_count": persisted_artifact.reuse_count,
                "reused_from_artifact_id": str(persisted_artifact.reused_from_artifact_id) if persisted_artifact.reused_from_artifact_id else None,
                "created_at": persisted_artifact.created_at.isoformat() if persisted_artifact.created_at else None,
                "generated_at": persisted_artifact.generated_at.isoformat() if persisted_artifact.generated_at else None,
            }
            
        except Exception as e:
            logger.error(f"Error creating artifact from narrative: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
        finally:
            db.close()
    
    def _build_artifact_content(
        self,
        context: DecisionContext,
        narrative: Dict[str, Any],
        is_valid: bool,
        errors: List[str]
    ) -> Dict[str, Any]:
        """
        Build structured content for AI Artifact.
        
        DOCUMENT 06A:
        Every AI Artifact SHALL contain:
        - Header
        - Business Content
        - Explainability
        - Supporting Evidence
        - Metadata
        """
        return {
            "header": {
                "title": f"Analysis Narrative - {context.business_objective}",
                "execution_id": str(context.execution_id),
                "workflow_id": context.workflow_id,
                "generated_at": context.generated_at.isoformat(),
                "language": context.language or "tr",
                "version": context.narrative_version or "1.0",
            },
            "business_content": {
                "summary": narrative.get("summary", ""),
                "findings": narrative.get("findings", []),
                "recommendations": narrative.get("recommendations", []),
                "metrics": narrative.get("metrics", {}),
                "insights": narrative.get("insights", []),
                "executive_summary": narrative.get("executive_summary", ""),
                "key_metrics": narrative.get("key_metrics", {}),
            },
            "explainability": {},  # Will be filled by ArtifactExplainability
            "supporting_evidence": {
                "execution_id": str(context.execution_id),
                "workflow_id": context.workflow_id,
                "business_objective": context.business_objective,
                "result_types": list(context.results.keys()) if context.results else [],
                "total_results": len(context.results) if context.results else 0,
                "validation_passed": is_valid,
                "validation_errors": errors if errors else [],
            },
            "metadata": {
                "prompt_version": context.prompt_version,
                "narrative_version": context.narrative_version,
                "llm_provider": context.llm_provider,
                "llm_model": context.llm_model,
                "model_version": context.model_version,
                "generation_type": "regenerated" if hasattr(context, 'regenerated') and context.regenerated else "initial",
                "user_id": str(context.user_id) if context.user_id else None,
                "company_id": str(context.company_id) if context.company_id else None,
            }
        }
    
    def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get AI Artifact by ID.
        
        DOCUMENT 06A: Artifact retrieval through repository.
        """
        try:
            db = SessionLocal()
            repository = ArtifactRepository(db)
            artifact = repository.get_by_id(artifact_id)
            
            if artifact:
                return {
                    "id": str(artifact.id),
                    "artifact_type": artifact.artifact_type,
                    "artifact_subtype": artifact.artifact_subtype,
                    "artifact_version": artifact.artifact_version,
                    "status": artifact.status,
                    "validation_status": artifact.validation_status,
                    "validation_errors": artifact.validation_errors,
                    "is_reused": artifact.is_reused,
                    "reuse_count": artifact.reuse_count,
                    "reused_from_artifact_id": str(artifact.reused_from_artifact_id) if artifact.reused_from_artifact_id else None,
                    "content": artifact.content,
                    "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                    "updated_at": artifact.updated_at.isoformat() if artifact.updated_at else None,
                    "generated_at": artifact.generated_at.isoformat() if artifact.generated_at else None,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting artifact: {e}")
            return None
        finally:
            db.close()
    
    def get_artifact_by_execution(self, execution_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get AI Artifact by execution ID.
        
        DOCUMENT 06A: Artifact retrieval through repository.
        """
        try:
            db = SessionLocal()
            repository = ArtifactRepository(db)
            artifact = repository.get_by_execution(execution_id)
            
            if artifact:
                return {
                    "id": str(artifact.id),
                    "artifact_type": artifact.artifact_type,
                    "artifact_subtype": artifact.artifact_subtype,
                    "artifact_version": artifact.artifact_version,
                    "status": artifact.status,
                    "validation_status": artifact.validation_status,
                    "is_reused": artifact.is_reused,
                    "reuse_count": artifact.reuse_count,
                    "content": artifact.content,
                    "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                    "generated_at": artifact.generated_at.isoformat() if artifact.generated_at else None,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting artifact by execution: {e}")
            return None
        finally:
            db.close()
    
    def list_artifacts(
        self,
        company_id: UUID,
        artifact_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List AI Artifacts by company.
        
        DOCUMENT 06A: Artifact listing through repository.
        """
        try:
            db = SessionLocal()
            repository = ArtifactRepository(db)
            
            if artifact_type:
                artifacts = repository.get_by_type(company_id, artifact_type, limit)
            else:
                artifacts = repository.get_by_company(company_id, limit, offset)
            
            return [
                {
                    "id": str(artifact.id),
                    "artifact_type": artifact.artifact_type,
                    "artifact_subtype": artifact.artifact_subtype,
                    "artifact_version": artifact.artifact_version,
                    "status": artifact.status,
                    "validation_status": artifact.validation_status,
                    "is_reused": artifact.is_reused,
                    "reuse_count": artifact.reuse_count,
                    "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                    "generated_at": artifact.generated_at.isoformat() if artifact.generated_at else None,
                }
                for artifact in artifacts
            ]
        except Exception as e:
            logger.error(f"Error listing artifacts: {e}")
            return []
        finally:
            db.close()
