import pytest

from framed.widgets.text.model import (
    LineTextModel,
    SimpleTextModel,
    TextLocation,
    TextModelError,
    TextRange,
)


# -- Test Single Line Model --
def test_line_model_constructor():
    model = LineTextModel()
    assert model.get() == ""

    model = LineTextModel("the default value")
    assert model.get() == "the default value"

    model = LineTextModel("line 1\nline 2")
    assert model.get() == "line 1"


def test_line_model_assign():
    model = LineTextModel()
    end = model.assign("text")
    assert end.line == 0
    assert end.col == 4

    end = model.assign("")
    assert end.line == 0
    assert end.col == 0


def test_line_model_insert():
    model = LineTextModel()
    result = model.insert(TextLocation(line=0, col=0), "some new text")
    assert result.after.line == 0
    assert result.after.col == 13
    assert result.remainder is None
    assert model.get() == "some new text"

    result = model.insert(TextLocation(line=0, col=5), "awesome ")
    assert result.after.line == 0
    assert result.after.col == 13
    assert result.remainder is None
    assert model.get() == "some awesome new text"

    with pytest.raises(TextModelError):
        model.insert(TextLocation(line=1, col=0), "out of range")

    with pytest.raises(TextModelError):
        model.insert(TextLocation(line=0, col=0), "\n")

    assert model.get(
        TextRange(
            TextLocation(line=0, col=5),
            TextLocation(line=0, col=12),
        )
    ) == "awesome"


def test_line_model_delete():
    model = LineTextModel("this is some boring text")
    model.delete(
        TextRange(
            TextLocation(line=0, col=13),
            TextLocation(line=0, col=20),
        )
    )
    assert model.get() == "this is some text"

    model.delete(
        TextRange(
            TextLocation(line=0, col=0),
            TextLocation(line=0, col=len(model.get()))
        )
    )
    assert model.get() == ""


# -- Test Simple Model --
def test_simple_model_constructor():
    model = SimpleTextModel()
    assert model.get() == ""

    model = SimpleTextModel("the default value")
    assert model.get() == "the default value"

    model = SimpleTextModel("line 1\nline 2")
    assert model.get() == "line 1\nline 2"


def test_simple_model_assign():
    model = SimpleTextModel()
    end = model.assign("line 1\nline 2")
    assert end.line == 1
    assert end.col == 6

    end = model.assign("line 1")
    assert end.line == 0
    assert end.col == 6

    end = model.assign("")
    assert end.line == 0
    assert end.col == 0


def test_simple_model_insert():
    model = SimpleTextModel()
    result = model.insert(TextLocation(line=0, col=0), "some new text")
    assert result.after.line == 0
    assert result.after.col == 13
    assert model.get() == "some new text"

    model.insert(TextLocation(line=0, col=5), "awesome ")
    assert model.get() == "some awesome new text"

    with pytest.raises(TextModelError):
        model.insert(TextLocation(line=1, col=1), "blah")

    assert model.get(
        TextRange(
            TextLocation(line=0, col=5),
            TextLocation(line=0, col=12),
        )
    ) == "awesome"

    result = model.insert(
        TextLocation(line=1, col=0),
        "the second line",
    )
    assert result.after.line == 1
    assert result.after.col == 15
    assert model.get() == "some awesome new text\nthe second line"

    assert model.get(
        TextRange(
            TextLocation(line=0, col=17),
            TextLocation(line=1, col=3)
        )
    ) == "text\nthe"

    with pytest.raises(TextModelError):
        model.get(
            TextRange(
                TextLocation(line=1, col=2),
                TextLocation(line=0, col=17)
            )
        )

    result = model.insert(
        TextLocation(line=1, col=15),
        "?"
    )
    assert result.after.line == 1
    assert result.after.col == 16
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
            end=TextLocation(line=1, col=0),
        )
    )
    assert model.get() == "line 2\nline 3"
    model.delete(
        TextRange(
            start=TextLocation(line=0, col=4),
            end=TextLocation(line=1, col=4)
        )
    )
    assert model.get() == "line 3"


def test_simple_model_insert_and_delete():
    model = SimpleTextModel()
    model.insert(TextLocation(line=0, col=0), "the first long line")
    model.delete(
        TextRange(
            TextLocation(line=0, col=10),
            TextLocation(line=0, col=15),
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
            TextLocation(line=1, col=4)
        )
    )
    assert model.get() == "the first edited line the second line"

