import copy
import unittest
from pathlib import Path
import tempfile
from aggregate import summarize
from runtime import Runtime, request
from claude_study import apply_usage
from study import prepare


class IntegrityTests(unittest.TestCase):
    def row(self,group='historical'):
        handoff={'reproducible':True,'impact_clear':True,'correction_checkable':True,'missing_information':[]}
        return {'id':'run-01','condition':'normal','group':group,'status':'completed','elapsed_seconds':100,
                'api_requests':2,'mutation_requests':0,'usage':[],
                'review':{'known':[{'id':'H1','identified':True,'actionable':True,'handoff':handoff}] if group=='historical' else [],
                          'additional':[],'coverage':'strong','passing_evidence':True,'bounded_conclusion':True,'access':{}}}

    def test_control_and_outage_do_not_inflate_discovery(self):
        result=summarize([self.row(),self.row('control'),self.row('outage')])['normal']
        self.assertEqual(result['runs'],3)
        self.assertEqual(result['historical_opportunities'],1)
        self.assertEqual(result['historical_actionable'],1)

    def test_unsupported_claim_gets_no_handoff_credit(self):
        row=self.row()
        claim={'classification':'unsupported','handoff':copy.deepcopy(row['review']['known'][0]['handoff'])}
        row['review']['additional']=[claim]
        result=summarize([row])['normal']
        self.assertEqual(result['additional'],{'unsupported':1})
        self.assertEqual(result['handoff_eligible'],1)
        self.assertEqual(result['handoff']['reproducible'],1)

    def test_missing_usage_remains_explicit(self):
        self.assertEqual(summarize([self.row()])['normal']['missing_usage'],1)

    def test_claude_budget_stop_is_not_a_completed_assessment(self):
        result={'status':'completed'}
        apply_usage(result,[{'type':'result','is_error':True,'subtype':'error_max_budget_usd',
                             'total_cost_usd':1.51,'usage':{'input_tokens':100,'cache_read_input_tokens':900,
                             'cache_creation_input_tokens':200,'output_tokens':40}}])
        self.assertEqual(result['status'],'budget-exhausted')
        self.assertEqual(result['cost_usd'],1.51)
        self.assertEqual(result['usage'][0]['input_tokens'],1200)
        self.assertEqual(result['usage_raw']['input_tokens'],100)

    def test_claude_absent_result_does_not_imply_success_or_free_execution(self):
        result={'status':'completed'}
        apply_usage(result,[])
        self.assertEqual(result['status'],'missing-client-result')
        self.assertIsNone(result['cost_usd'])
        self.assertEqual(result['usage'],[])

    def test_head_preserves_outage_status_and_is_audited(self):
        with tempfile.TemporaryDirectory(prefix='history-head-test-') as temp:
            with Runtime('/unused',Path(temp)/'control',outage=True) as runtime:
                response=request(runtime.url+'/users/me','HEAD')
                self.assertEqual(response['status'],503)
                self.assertEqual(response['body'],'')
            self.assertEqual(len(runtime.audit),1)
            self.assertEqual(runtime.audit[0]['method'],'HEAD')

    def test_prepare_rejects_missing_compiled_artifacts_before_creating_study(self):
        with tempfile.TemporaryDirectory(prefix='history-build-test-') as temp:
            root=Path(temp)
            with self.assertRaisesRegex(FileNotFoundError,'Missing compiled historical artifacts'):
                prepare(root/'study',root/'empty-build')
            self.assertFalse((root/'study').exists())


if __name__=='__main__':
    unittest.main()
