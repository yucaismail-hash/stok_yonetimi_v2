"""
Create AI Artifacts Table - DOCUMENT 06A
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    op.create_table(
        'ai_artifacts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_deleted', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        
        # Common Metadata
        sa.Column('artifact_type', sa.String, nullable=False),
        sa.Column('artifact_subtype', sa.String, nullable=True),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', UUID(as_uuid=True), nullable=True),
        sa.Column('execution_id', UUID(as_uuid=True), nullable=True),
        sa.Column('language', sa.String, default='tr'),
        
        # Versioning
        sa.Column('prompt_version', sa.String, nullable=True),
        sa.Column('schema_version', sa.String, default='1.0'),
        sa.Column('communication_contract_version', sa.String, default='1.0'),
        sa.Column('artifact_version', sa.Integer, default=1),
        
        # LLM Provider
        sa.Column('llm_provider', sa.String, nullable=True),
        sa.Column('llm_model', sa.String, nullable=True),
        sa.Column('model_version', sa.String, nullable=True),
        
        # Content
        sa.Column('content', JSONB, nullable=False),
        
        # Status & Validation
        sa.Column('status', sa.String, default='draft'),
        sa.Column('validation_status', sa.String, nullable=True),
        sa.Column('validation_errors', JSONB, nullable=True),
        sa.Column('validated_at', sa.DateTime, nullable=True),
        sa.Column('validated_by', UUID(as_uuid=True), nullable=True),
        
        # Reuse
        sa.Column('is_reused', sa.Boolean, default=False),
        sa.Column('reused_from_artifact_id', UUID(as_uuid=True), nullable=True),
        sa.Column('reuse_count', sa.Integer, default=0),
        
        # Audit
        sa.Column('generated_by', UUID(as_uuid=True), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id']),
        sa.ForeignKeyConstraint(['execution_id'], ['execution_results.id']),
        sa.ForeignKeyConstraint(['validated_by'], ['users.id']),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id']),
        sa.ForeignKeyConstraint(['reused_from_artifact_id'], ['ai_artifacts.id']),
    )
    
    # Indexes
    op.create_index('ix_ai_artifacts_company_type_status', 'ai_artifacts', ['company_id', 'artifact_type', 'status'])
    op.create_index('ix_ai_artifacts_company_execution', 'ai_artifacts', ['company_id', 'execution_id'])
    op.create_index('ix_ai_artifacts_company_dataset', 'ai_artifacts', ['company_id', 'dataset_id'])
    op.create_index('ix_ai_artifacts_created_at', 'ai_artifacts', ['created_at'])


def downgrade():
    op.drop_table('ai_artifacts')