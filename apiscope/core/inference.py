"""Schema inference helpers and optional field-aware merging."""
from apiscope.core.mvp_analysis import infer, merge_schemas

def infer_from_samples(samples):
    return merge_schemas([infer(sample) for sample in samples])

def confidence(observations, schema_stability=1.0, source_count=1):
    """Heuristic confidence; not an accuracy claim."""
    evidence=min(max(observations,0),20)/20
    sources=min(max(source_count,1),3)/3
    return round(max(0.0,min(0.99,0.25+0.4*evidence+0.2*schema_stability+0.14*sources)),2)
