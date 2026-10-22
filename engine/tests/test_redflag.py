import pytest

from happygut_engine import check_red_flags

POSITIVE = [
    # heavy bleeding
    ("There is a lot of blood in my stool today", "heavy_bleeding"),
    ("bloody diarrhoea since morning", "heavy_bleeding"),
    ("I'm bleeding heavily from my bottom", "heavy_bleeding"),
    ("vomiting blood", "heavy_bleeding"),
    ("পায়খানার সাথে অনেক রক্ত যাচ্ছে", "heavy_bleeding"),
    ("রক্ত বমি হচ্ছে", "heavy_bleeding"),
    ("paikhana er sathe rokto jacche", "heavy_bleeding"),
    ("onek rokto porche", "heavy_bleeding"),
    # fever with abdominal pain
    ("I have a fever and severe stomach pain", "fever_with_abdominal_pain"),
    ("high temperature and abdominal cramps", "fever_with_abdominal_pain"),
    ("জ্বর আর পেটে ব্যথা", "fever_with_abdominal_pain"),
    ("jor ase ar pete betha", "fever_with_abdominal_pain"),
    # possible obstruction
    ("I keep vomiting and can't pass gas", "possible_obstruction"),
    ("belly pain and no bowel movement for two days", "possible_obstruction"),
    ("বমি হচ্ছে আর পায়খানা হচ্ছে না", "possible_obstruction"),
    ("bomi hocche, gas ber hocche na", "possible_obstruction"),
    # severe dehydration
    ("I'm severely dehydrated and can't keep water down", "severe_dehydration"),
    ("I fainted after the diarrhoea", "severe_dehydration"),
    ("সারাদিন প্রস্রাব হচ্ছে না", "severe_dehydration"),
    ("pani shunnota hoye geche", "severe_dehydration"),
]

NEGATIVE = [
    "I ate rice and dal for lunch",
    "ajke dupure kacchi khabo",
    "আজ দুপুরে খিচুড়ি খেয়েছি",
    "I have a blood test tomorrow",
    "my stomach is fine today",
    "a bit of fever, nothing else",
    "spicy food gives me some bloating",
]


@pytest.mark.parametrize("text,category", POSITIVE)
def test_red_flags_detected(text, category):
    result = check_red_flags(text)
    assert result.triggered, text
    assert category in result.categories


@pytest.mark.parametrize("text", NEGATIVE)
def test_normal_messages_do_not_trigger(text):
    assert not check_red_flags(text).triggered


def test_recall_on_suite_is_100_percent():
    hits = sum(check_red_flags(t).triggered for t, _ in POSITIVE)
    assert hits == len(POSITIVE)


def test_unicode_variants_of_bangla_letters_match():
    # য় can be typed as one code point (U+09DF) or as য + nukta; both must match.
    composed = "পায়খানা"  # পায়খানা with U+09DF
    decomposed = "পায়খানা"
    for word in (composed, decomposed):
        assert check_red_flags(f"{word}র সাথে অনেক রক্ত").triggered
