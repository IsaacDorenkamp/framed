import pytest

from framed.widgets.text.model import (
    SimpleTextModel,
    TextLocation,
    TextModelError,
    TextRange,
)


# -- Test Simple Model --
def test_simple_model_constructor():
    model = SimpleTextModel()
    assert model.get() == ""

    model = SimpleTextModel("the default value")
    assert model.get() == "the default value"

    model = SimpleTextModel("line 1\nline 2")
    assert model.get() == "line 1\nline 2"


def test_simple_model_insert():
    model = SimpleTextModel()
    model.insert(TextLocation(line=0, col=0), "some new text")
    assert model.get() == "some new text"

    model.insert(TextLocation(line=0, col=5), "awesome ")
    assert model.get() == "some awesome new text"

    with pytest.raises(TextModelError):
        model.insert(TextLocation(line=1, col=1), "blah")

    assert model.get(
        TextRange(
            TextLocation(line=0, col=5),
            TextLocation(line=0, col=11),
        )
    ) == "awesome"

    model.insert(
        TextLocation(line=1, col=0),
        "the second line",
    )
    assert model.get() == "some awesome new text\nthe second line"

    assert model.get(
        TextRange(
            TextLocation(line=0, col=17),
            TextLocation(line=1, col=2)
        )
    ) == "text\nthe"

    with pytest.raises(TextModelError):
        model.get(
            TextRange(
                TextLocation(line=1, col=2),
                TextLocation(line=0, col=17)
            )
        )

    model.insert(
        TextLocation(line=1, col=15),
        "?"
    )
    assert model.get() == "some awesome new text\nthe second line?"


def test_simple_model_insert_blank():
    model = SimpleTextModel()
    model.insert(
        TextLocation(line=0, col=0),
        "\n"
    )
    assert model.get() == "\n"

    model.insert(
        TextLocation(line=0, col=0),
        "\n\n",
    )
    assert model.get() == "\n\n\n"

    model.insert(
        TextLocation(line=1, col=0),
        "some text",
    )
    assert model.get() == "\nsome text\n\n"


def test_simple_model_delete():
    model = SimpleTextModel("line 1\nline 2\nline 3")
    model.delete(
        TextRange(
            start=TextLocation(line=0, col=0),
            end=TextLocation(line=0, col=6),
        )
    )
    assert model.get() == "line 2\nline 3"
    model.delete(
        TextRange(
            start=TextLocation(line=0, col=4),
            end=TextLocation(line=1, col=3)
        )
    )
    assert model.get() == "line 3"



def test_simple_model_insert_and_delete():
    model = SimpleTextModel()
    model.insert(TextLocation(line=0, col=0), "the first long line")
    model.delete(
        TextRange(
            TextLocation(line=0, col=10),
            TextLocation(line=0, col=14),
        )
    )
    assert model.get() == "the first line"
    model.insert(TextLocation(line=0, col=9), " edited")
    assert model.get() == "the first edited line"
    model.insert(TextLocation(line=1, col=0), "now, the second line")
    assert model.get() == "the first edited line\nnow, the second line"
    model.delete(
        TextRange(
            TextLocation(line=0, col=21),
            TextLocation(line=1, col=3)
        )
    )
    assert model.get() == "the first edited line the second line"

