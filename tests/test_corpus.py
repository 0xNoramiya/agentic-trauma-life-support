"""Tests for corpus ingestion heuristics.

The bibliography-filter is new and easy to over- or under-fit; a few
fixture-driven tests pin it down.
"""

from __future__ import annotations

from ats.corpus.ingest import _looks_like_references


def test_filter_keeps_substantive_prose():
    """Body text with one or two year mentions should pass through."""
    text = (
        "Tension pneumothorax is a clinical diagnosis. Treatment must not be "
        "delayed for radiographic confirmation. Immediate decompression of "
        "the affected hemithorax is required. The 2011 update of the EAST "
        "guideline reaffirms this approach."
    )
    assert _looks_like_references(text) is False


def test_filter_drops_dense_year_citations():
    """A chunk with many year mentions is treated as a reference list."""
    text = (
        "Smith et al. 2009; Jones et al. 2010; Williams et al. 2011; "
        "Brown et al. 2012; Davis et al. 2013; Miller et al. 2014."
    )
    assert _looks_like_references(text) is True


def test_filter_drops_numbered_list_entries():
    """Numbered bibliography rows."""
    text = (
        "1. Smith JA. Pulmonary contusion management.\n"
        "2. Jones BB. Flail chest outcomes.\n"
        "3. Williams CC. Trauma in the elderly.\n"
        "4. Brown DD. Hemothorax follow-up.\n"
        "5. Davis EE. Rib fracture analgesia.\n"
        "6. Miller FF. Tube thoracostomy review."
    )
    assert _looks_like_references(text) is True


def test_filter_keeps_recommendations_text():
    """Real EAST PMG recommendation prose should pass through."""
    text = (
        "Patients with PC-FC should not be excessively fluid restricted but "
        "rather should be resuscitated as necessary with isotonic crystalloid "
        "or colloid solution to maintain signs of adequate tissue perfusion. "
        "Once adequately resuscitated, unnecessary fluid administration should "
        "be meticulously avoided."
    )
    assert _looks_like_references(text) is False
