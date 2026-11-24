from fastapi.testclient import TestClient
from contradiction_lab import api
from contradiction_lab.cli import DEMO_QUERY
from contradiction_lab.evaluation.runner import evaluate,score

def test_api_roundtrip(engine,monkeypatch):
    monkeypatch.setattr(api,'get_engine',lambda:engine)
    with TestClient(api.app) as client:
        assert client.get('/health').json()['model_backend']=='ollama'
        assert 'Evidence is rarely binary' in client.get('/').text
        result=client.post('/research',json={'query':DEMO_QUERY,'workflow':'static'}).json()
        assert client.get('/research/'+result['run_id']).json()==result
        assert client.get('/research/'+result['run_id']+'/trace').status_code==200
        assert client.get('/research/missing').status_code==404
        assert client.post('/research',json={'query':DEMO_QUERY,'top_k':0}).status_code==422

def test_evaluation_scores_actual_outputs(engine):
    result=engine.run(__import__('contradiction_lab.schemas',fromlist=['ResearchRequest']).ResearchRequest(query=DEMO_QUERY))
    row=score({'case_id':'test','expected_status':'evidence_found'},result)
    assert row['passed'] and row['input_tokens']>0
    result['report']['claims'][0]['claim_id']='unverified'
    assert not score({'case_id':'bad'},result)['passed']
