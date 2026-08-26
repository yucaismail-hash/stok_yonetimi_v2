"""Persisted readiness evaluation for Business Workflow tasks."""
from app.engine.runtime_store import RuntimeStore
class BusinessWorkflowReadinessError(ValueError): pass
class BusinessWorkflowScheduler:
 def __init__(self,session,runner_factory=None):
  self.store=RuntimeStore(session)
  self._runner_factory=runner_factory
 def readiness(self,execution_id,company_id):
  execution=self.store.get_execution(execution_id,company_id)
  if not execution: raise BusinessWorkflowReadinessError('execution unavailable')
  tasks=self.store.get_tasks(execution_id,company_id); by_id={t.task_id:t for t in tasks}; refs=self.store.get_execution_result_references(execution_id,company_id); validated={r.result_type for r in refs if r.validation_status=='validated'}; out=[]
  for task in tasks:
   blocked=[]
   for dep in task.dependencies:
    parent=by_id.get(dep)
    if not parent: raise BusinessWorkflowReadinessError(f'missing dependency target: {dep}')
    if parent.state!='completed': blocked.append(dep);continue
    expected='forecast' if dep=='forecast' else dep
    if expected not in validated: blocked.append(dep+':validated_result_missing')
   ready=execution.state not in ('completed','failed','cancelled') and task.state=='pending' and not task.lease_token and not blocked
   out.append({'task_id':task.task_id,'capability':task.capability,'state':task.state,'ready':ready,'blocking_dependencies':blocked,'required_upstream_results':[x for x in task.dependencies],'task_order':task.task_order})
  return out
 async def run_next_ready(self,execution_id,company_id):
  execution=self.store.get_execution(execution_id,company_id)
  if execution and execution.state=='completed' and execution.analysis_type=='business_workflow':
   # Terminal workflows have no analytical task to claim; this is the bounded
   # recovery entry point for advisory Decision finalization only.
   from app.application.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalizationService
   BusinessWorkflowDecisionFinalizationService().finalize(company_id,execution_id)
   return None
  ready=[row for row in self.readiness(execution_id,company_id) if row['ready']]
  if not ready:return None
  row=ready[0]
  if row['capability'] not in ('demand_forecast','safety_stock','supplier','simulation','backtest'): raise BusinessWorkflowReadinessError('unsupported business capability')
  # Reuse the verified runner lifecycle for the first durable task only.
  if self._runner_factory is None:
   from app.engine.local_forecast_runner import LocalForecastRunner
   runner=LocalForecastRunner()
  else: runner=self._runner_factory()
  return await runner.run_business_task(execution_id,company_id,row['task_id'])
