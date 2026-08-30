from src.model.predict import build_prediction
from src.nlp.render import DISCLAIMER_SHORT, render_paquete

CSV_PATH = "data/raw/demo_matches.csv"
COMPETITION = "DEMO"


def test_render_paquete_includes_all_markets_and_disclaimer():
    prediction = build_prediction(CSV_PATH, COMPETITION, "demo_team_01", "demo_team_02")
    text = render_paquete(prediction)

    assert "1X2" in text
    assert "Ambos marcan" in text
    assert "línea 2.5" in text
    assert "Marcadores más probables" in text
    assert DISCLAIMER_SHORT in text

    prohibidas = ["apuesta esto", "está cantado", "te aseguro", "ganancia segura"]
    lowered = text.lower()
    for frase in prohibidas:
        assert frase not in lowered
