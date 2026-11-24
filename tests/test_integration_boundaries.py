from contradiction_lab.graph import ResearchEngine
from contradiction_lab.llm import ModelError,OllamaModel
from contradiction_lab.schemas import ResearchRequest
from contradiction_lab.providers import deduplicate

def test_missing_model_never_substitutes_answers(settings,mocked_models,monkeypatch):
    def unavailable(*a,**kw): raise ModelError('Injected unavailable model')
    monkeypatch.setattr(OllamaModel,'structured',unavailable)
    result=ResearchEngine(settings).run(ResearchRequest(query='Compare diversity and productivity'))
    assert result['status']=='insufficient_evidence'
    assert not result['report']['claims']
    assert any(e['kind']=='model_error' for e in result['errors'])

def test_same_titles_with_different_dois_not_merged(corpus):
    left=corpus.papers[0]; right=left.model_copy(update={'doi':'10.1234/different','provider_id':'different'})
    assert len(deduplicate([left,right]))==2
