# app/decision_intelligence/prompt_manager.py
"""
Prompt Manager - DOCUMENT 06 - PART 01
Manages prompt templates, versions, selection and composition.
"""

from typing import Dict, Any, Optional, List
import json
import os
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.narrative_payload_builder import NarrativePayloadBuilder

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Prompt Manager - DOCUMENT 06
    
    Manages prompt templates, versions, selection and composition.
    Future prompt changes do NOT require Decision Intelligence modifications.
    """
    
    def __init__(self, prompts_dir: str = "app/decision_intelligence/prompts"):
        self.prompts_dir = prompts_dir
        self.payload_builder = NarrativePayloadBuilder()
        self._templates: Dict[str, str] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load prompt templates from files."""
        template_files = [
            "base_prompt.txt",
            "executive_summary.txt",
            "findings.txt",
            "risks.txt",
            "opportunities.txt",
            "recommendations.txt",
            "timeline.txt",
            "advisor.txt",
        ]
        
        for filename in template_files:
            filepath = os.path.join(self.prompts_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._templates[filename.replace('.txt', '')] = f.read()
                logger.info(f"✅ Loaded prompt template: {filename}")
            except FileNotFoundError:
                logger.warning(f"⚠️ Prompt template not found: {filename}")
                self._templates[filename.replace('.txt', '')] = self._get_default_template(filename)
    
    def _get_default_template(self, filename: str) -> str:
        """Get default template if file not found."""
        defaults = {
            "base_prompt": "You are Stokonomi AI, a supply chain decision assistant.",
            "executive_summary": "Provide an executive summary of the analysis results.",
            "findings": "What are the key findings from the analysis?",
            "risks": "What are the main risks identified?",
            "opportunities": "What opportunities were identified?",
            "recommendations": "What actions do you recommend?",
            "timeline": "What is the recommended timeline for actions?",
            "advisor": "Act as a senior supply chain advisor."
        }
        return defaults.get(filename.replace('.txt', ''), "")
    
    def build_prompt(
        self,
        context: DecisionContext,
        prompt_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build prompt for LLM.
        
        Args:
            context: DecisionContext with all results
            prompt_type: Type of prompt to build (executive_summary, findings, etc.)
        
        Returns:
            Dict with prompt, system_prompt, and metadata
        """
        # 1. Build payload
        payload = self.payload_builder.build(context)
        
        # 2. Select prompt type
        prompt_type = prompt_type or context.metadata.get("prompt_type", "executive_summary")
        
        # 3. Get templates
        base_template = self._templates.get("base_prompt", "")
        specific_template = self._templates.get(prompt_type, "")
        advisor_template = self._templates.get("advisor", "")
        
        # 4. Get language instruction
        language_instruction = self._get_language_instruction(context.user_language)
        
        # 5. Get business objective description
        objective_description = self._get_objective_description(context.business_objective)
        
        # 6. Build system prompt
        system_prompt = self._build_system_prompt(
            base_template,
            advisor_template,
            language_instruction,
            objective_description,
        )
        
        # 7. Build user prompt
        user_prompt = self._build_user_prompt(
            specific_template,
            payload,
            prompt_type,
            context,
        )
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "prompt_type": prompt_type,
            "prompt_version": context.prompt_version,
            "language": context.user_language,
            "payload": payload,
        }
    
    def _build_system_prompt(
        self,
        base: str,
        advisor: str,
        language: str,
        objective: str,
    ) -> str:
        """Build system prompt."""
        parts = []
        
        if base:
            parts.append(base)
        if advisor:
            parts.append(advisor)
        
        parts.append(f"Language: {language}")
        parts.append(f"Business Objective: {objective}")
        
        # Add rules
        parts.append("""
RULES:
- DO NOT calculate any inventory values, safety stock, or forecast numbers.
- DO NOT generate new numbers or statistics.
- ONLY use the provided analysis results and statistics.
- Your task is to INTERPRET and EXPLAIN the results.
- Act as a senior consultant presenting findings to the C-suite.
- Use business language, avoid technical jargon.
- Preserve all numerical values from the analysis.
""")
        
        return "\n\n".join(parts)
    
    def _build_user_prompt(
        self,
        template: str,
        payload: Dict[str, Any],
        prompt_type: str,
        context: DecisionContext,
    ) -> str:
        """Build user prompt."""
        # Format payload as JSON
        payload_json = json.dumps(payload, indent=2, ensure_ascii=False)
        
        # Build prompt
        prompt_parts = []
        
        if template:
            prompt_parts.append(template)
        
        prompt_parts.append(f"Analysis Results:\n{payload_json}")
        
        # Add specific instructions based on prompt type
        instructions = self._get_prompt_instructions(prompt_type, context)
        if instructions:
            prompt_parts.append(f"\nInstructions:\n{instructions}")
        
        # Add output format instructions
        prompt_parts.append("""
Output Format:
Return ONLY valid JSON with the following structure:
{
  "summary": "Executive summary (2-3 sentences)",
  "findings": ["finding1", "finding2", ...],
  "risks": ["risk1", "risk2", ...],
  "opportunities": ["opportunity1", "opportunity2", ...],
  "recommendations": ["recommendation1", "recommendation2", ...],
  "timeline": "Recommended timeline (e.g., 'Immediate', 'Next 30 days')",
  "confidence": 0.95
}
""")
        
        return "\n\n".join(prompt_parts)
    
    def _get_language_instruction(self, language: str) -> str:
        """Get language instruction."""
        instructions = {
            "Türkçe": "Lütfen tüm yanıtlarını TÜRKÇE olarak ver.",
            "English": "Please respond in ENGLISH.",
            "Deutsch": "Bitte antworte auf DEUTSCH.",
            "Français": "Veuillez répondre en FRANÇAIS.",
        }
        return instructions.get(language, instructions["Türkçe"])
    
    def _get_objective_description(self, objective: str) -> str:
        """Get business objective description."""
        descriptions = {
            "demand_forecast": "Demand Forecast Analysis",
            "safety_stock_optimization": "Safety Stock Optimization",
            "inventory_optimization": "Inventory Optimization",
            "supplier_optimization": "Supplier Optimization",
            "simulation_scenario": "Simulation Scenario Analysis",
        }
        return descriptions.get(objective, objective.replace("_", " ").title())
    
    def _get_prompt_instructions(self, prompt_type: str, context: DecisionContext) -> str:
        """Get specific instructions for prompt type."""
        instructions = {
            "executive_summary": "Provide a concise executive summary (2-3 sentences) that captures the most important insights.",
            "findings": "List the key findings from the analysis (max 5 items).",
            "risks": "Identify the main risks (max 5 items).",
            "opportunities": "Identify the main opportunities (max 5 items).",
            "recommendations": "Provide actionable recommendations (max 5 items).",
            "timeline": "Provide a recommended timeline for actions.",
        }
        return instructions.get(prompt_type, "")
    
    def get_template(self, name: str) -> Optional[str]:
        """Get a prompt template by name."""
        return self._templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List all available prompt templates."""
        return list(self._templates.keys())