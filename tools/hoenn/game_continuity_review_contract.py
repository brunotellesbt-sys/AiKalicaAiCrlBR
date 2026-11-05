"""Pinned layer-167 identities for the campaign/coastal-camera follow-up."""
SCOPE = 'game-continuity-review'
HISTORICAL_COMMIT = 'b0e1c565853826b14ab19c8f0e5eee6df5abc4f4'
PARENT_ROM_SHA256 = '9ade93b456c32bc41868642dabb287e0297cba8ebbeda97aa478bd6b11c678f5'
PARENT_ELF_SHA256 = 'b441e07a811665f170114eba582e26165081a34d0077a7df6d2f1c46500c7b8e'
PARENT_MARKER_SHA256 = '4ce7345f69dfef340946567c58e8017db040985f2030179aaeb4e052d757147c'
BASELINE_SHA256 = {
    'versions.json': 'a80d5c1c83a5bd9c3b35eda7e306b1c5d98ea5931c0fbe2916c80f2cc087f470',
    'review.json': '8521361f0ee4a18a64328c1f4f791550b005c92878bb08487d40a433cf534629',
    'test.sav': 'cf563eb3ab67dba771c12022dd1aed7d9e27ad7fb62419cc453198543a8985cc',
}
# Root pins exact reviewed paths/bytes after the repair helpers are complete.
PREPARED_SHA256 = {'data/layouts/layouts.json': '9e1d18215ac45d1041cc9540d3cd42d36694425090d08f6d55b53fe56600f0ac',
 'include/journey_campaign_gates.h': '30540818b576e77b9c2609949371dc1b47db71339b05bf46b8f09f8fe1ede224',
 'src/journey_campaign_gates.c': '231c00b201e04881553d575c90dbdeaddfe2b395114b22589c60cfb142656c19',
 'src/journey_story_continuity.c': 'e3ff8a5f0307b013811d7e2db5fb4935a5462fd56de70088f7bbe0905956b847'}
# The actual campaign and camera report schemas must be reviewed first.
NATIVE_CONTRACT_FINALIZED = True
