# app/decision_intelligence/communication_contract/prompt_manager.py
"""
Prompt Manager - DOCUMENT 06 - PART 05
"""

from typing import Dict, Any, Optional
import json
import logging

from app.decision_intelligence.communication_contract.policy import CommunicationPolicy
from app.decision_intelligence.communication_contract.prompt_version_manager import PromptVersionManager

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Prompt Manager - CP-002
    
    Manages prompt templates, composition, and lifecycle.
    """
    
    def __init__(self):
        self.policy = CommunicationPolicy()
        self.version_manager = PromptVersionManager()
        self._templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load prompt templates."""
        return {
            "base": self.policy.get_policy_statement(),
            "executive_summary": """
Provide an executive summary that answers:
1. What happened?
2. Why does it matter?
3. What should management know?

Be concise and business-focused.
""",
            "findings": """
List the key findings from the analysis.
Each finding must be supported by analytical evidence.
Use business language.
""",
            "risks": """
Identify business risks with:
- Risk description
- Business impact
- Supporting evidence
- Priority level
""",
            "opportunities": """
Identify business opportunities with:
- Opportunity description
- Expected benefit
- Business value
- Supporting evidence
""",
            "recommendations": """
Provide recommendations with:
- Recommended action
- Reason
- Expected benefit
- Supporting evidence
""",
            "advisor": """
Act as a strategic advisor to the CEO.
Provide strategic guidance based on historical evidence.
Focus on long-term business evolution.
""",
        }
    
    def build_prompt(self, context, payload: Dict[str, Any], prompt_type: str = "executive_summary") -> Dict[str, Any]:
        """
        Build prompt for LLM.
        """
        # 1. Get templates
        base_template = self._templates.get("base", "")
        specific_template = self._templates.get(prompt_type, "")
        
        # 2. Get policy statement
        policy_statement = self.policy.get_policy_statement()
        
        # 3. Build system prompt
        system_prompt = f"""
{policy_statement}

{base_template}

Language: {context.user_language}
Prompt Version: {self.version_manager.get_current_version()}
"""
        
        # 4. Build user prompt
        payload_json = json.dumps(payload, indent=2, ensure_ascii=False)
        
        user_prompt = f"""
{specific_template}

Analysis Data:
{payload_json}

Return ONLY valid JSON matching the expected schema.
Do NOT include any text outside the JSON.
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "prompt_type": prompt_type,
            "prompt_version": self.version_manager.get_current_version(),
        }
    
    def get_template(self, name: str) -> Optional[str]:
        """Get a prompt template."""
        return self._templates.get(name)