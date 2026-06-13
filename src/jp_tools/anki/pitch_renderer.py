"""Convert a Kanjium pitch-accent downstep number into an HTML span diagram.

Pitch accent patterns (downstep = N):
  0  heiban    L H H H H...  (never drops)
  1  atamadaka H L L L L...
  2+ nakadaka  L H...H L L...  (drops after mora N)

  For N == mora_count: odaka (L H H H H) — drops after the last mora (audible on particle).

The output is a single <span> with inline CSS that renders a high/low contour
using CSS border-top (overline on high moras).
"""


def _split_morae(hiragana: str) -> list[str]:
    """Split hiragana string into morae, treating digraphs (きゃ, etc.) as one mora."""
    digraph_second = set("ぁぃぅぇぉゃゅょァィゥェォャュョ")
    morae = []
    i = 0
    while i < len(hiragana):
        if i + 1 < len(hiragana) and hiragana[i + 1] in digraph_second:
            morae.append(hiragana[i: i + 2])
            i += 2
        else:
            morae.append(hiragana[i])
            i += 1
    return morae


def _pitch_pattern(mora_count: int, downstep: int) -> list[bool]:
    """Return a list of booleans (True = high) for each mora position."""
    if mora_count == 0:
        return []
    if downstep == 0:
        # heiban: first mora low, rest high
        return [False] + [True] * (mora_count - 1)
    if downstep == 1:
        # atamadaka: first mora high, rest low
        return [True] + [False] * (mora_count - 1)
    # nakadaka / odaka: first mora low, high until downstep, then low
    result = [False]
    for i in range(1, mora_count):
        result.append(i < downstep)
    return result


_HIGH_STYLE = "border-top:2px solid currentColor;padding-top:1px;"
_LOW_STYLE = ""


def render_pitch_html(reading_hiragana: str, downstep: int | None) -> str:
    """Return an HTML string with pitch accent markup, or plain reading if downstep is None."""
    if not reading_hiragana:
        return ""
    if downstep is None:
        return f"<span class='pitch'>{reading_hiragana}</span>"

    morae = _split_morae(reading_hiragana)
    if not morae:
        return reading_hiragana

    pattern = _pitch_pattern(len(morae), downstep)
    parts = []
    for mora, high in zip(morae, pattern):
        style = _HIGH_STYLE if high else _LOW_STYLE
        if style:
            parts.append(f"<span style='{style}'>{mora}</span>")
        else:
            parts.append(mora)

    label = f"[{downstep}]"
    return f"<span class='pitch' title='{label}'>{''.join(parts)}</span>"
