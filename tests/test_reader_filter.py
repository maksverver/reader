import pytest
from fakeparser import Parser
from reader_methods import get_feeds
from utils import rename_argument
from utils import utc_datetime as datetime


ALL_IDS = {(1, 1), (1, 2), (2, 1), (3, 1)}

TAGS_AND_EXPECTED_IDS = [
    (None, ALL_IDS),
    ([], ALL_IDS),
    ([[]], ALL_IDS),
    (True, ALL_IDS - {(3, 1)}),
    ([True], ALL_IDS - {(3, 1)}),
    (False, {(3, 1)}),
    ([False], {(3, 1)}),
    ([True, False], set()),
    ([[True, False]], ALL_IDS),
    (['tag'], ALL_IDS - {(3, 1)}),
    ([['tag']], ALL_IDS - {(3, 1)}),
    (['tag', 'tag'], ALL_IDS - {(3, 1)}),
    ([['tag'], ['tag']], ALL_IDS - {(3, 1)}),
    ([['tag', 'tag']], ALL_IDS - {(3, 1)}),
    (['-tag'], {(3, 1)}),
    (['unknown'], set()),
    (['-unknown'], ALL_IDS),
    (['first'], {(1, 1), (1, 2)}),
    (['second'], {(2, 1)}),
    (['first', 'second'], set()),
    ([['first'], ['second']], set()),
    ([['first', 'second']], {(1, 1), (1, 2), (2, 1)}),
    (['first', 'tag'], {(1, 1), (1, 2)}),
    (['second', 'tag'], {(2, 1)}),
    ([['first', 'second'], 'tag'], {(1, 1), (1, 2), (2, 1)}),
    ([['first'], ['tag']], {(1, 1), (1, 2)}),
    ([['first', 'tag']], {(1, 1), (1, 2), (2, 1)}),
    (['-first', 'tag'], {(2, 1)}),
    ([['first', '-tag']], ALL_IDS - {(2, 1)}),
    ([[False, 'first']], {(1, 1), (1, 2), (3, 1)}),
    ([True, '-first'], {(2, 1)}),
]


def resource_ids_to_int(resource_ids):
    return {tuple(map(eval, rid)) for rid in resource_ids}


@pytest.fixture
def reader_for_tags(reader):
    reader._parser = parser = Parser()

    one = parser.feed(1, datetime(2010, 1, 1))  # tag, first
    one_one = parser.entry(1, '1', datetime(2010, 1, 1))
    one_two = parser.entry(1, '2', datetime(2010, 2, 1))

    two = parser.feed(2, datetime(2010, 1, 1))  # tag, second
    two_one = parser.entry(2, '1', datetime(2010, 1, 1))

    three = parser.feed(3, datetime(2010, 1, 1))  # <no tags>
    three_one = parser.entry(3, '1', datetime(2010, 1, 1))

    for feed in one, two, three:
        reader.add_feed(feed)

    reader.update_feeds()
    return reader


@pytest.fixture
@rename_argument('reader', 'reader_for_tags')
def reader_feed_tags(reader):
    reader.set_tag('1', 'tag')
    reader.set_tag('1', 'first')
    reader.set_tag('2', 'tag')
    reader.set_tag('2', 'second')
    return reader


@pytest.mark.parametrize('tags, expected', TAGS_AND_EXPECTED_IDS)
@rename_argument('reader', 'reader_feed_tags')
def test_entries_by_feed_tags(reader, get_entries, tags, expected):
    get_entries.after_update(reader)

    resource_ids = [e.resource_id for e in get_entries(reader, feed_tags=tags)]
    assert resource_ids_to_int(resource_ids) == expected, tags

    if tags is None:
        assert resource_ids == [e.resource_id for e in get_entries(reader)]


# TODO: maybe test all the get_feeds sort orders (maybe fixture?)


@pytest.mark.parametrize('get_feeds', [get_feeds])
@pytest.mark.parametrize('tags, expected', TAGS_AND_EXPECTED_IDS)
@rename_argument('reader', 'reader_feed_tags')
def test_feeds_by_tags(reader, get_feeds, tags, expected):
    get_feeds.after_update(reader)

    resource_ids = [f.resource_id for f in get_feeds(reader, tags=tags)]
    assert resource_ids_to_int(resource_ids) == {t[:1] for t in expected}, tags

    if tags is None:
        assert resource_ids == [f.resource_id for f in get_feeds(reader)]


def test_entry_tags_basic(reader):
    # roughly modeled after test_filtering_tags

    reader._parser = parser = Parser()

    one = parser.feed(1, datetime(2010, 1, 1))
    one_one = parser.entry(1, 1, datetime(2010, 1, 1))
    one_two = parser.entry(1, 2, datetime(2010, 2, 1))
    two = parser.feed(2, datetime(2010, 1, 1))
    two_one = parser.entry(2, 1, datetime(2010, 1, 1))

    for feed in one, two:
        reader.add_feed(feed)

    reader.update_feeds()

    reader.set_tag(one_one, 'tag')
    reader.set_tag(one_one, 'first')
    reader.set_tag(two_one, 'tag')
    reader.set_tag(two_one, 'second')

    def get(tags):
        return {e.id for e in reader.get_entries(tags=tags)}

    assert get(None) == {'1, 1', '1, 2', '2, 1'}
    assert get(['tag']) == {'1, 1', '2, 1'}
    assert get(['first']) == {'1, 1'}
    assert get(['second']) == {'2, 1'}
    assert get(True) == {'1, 1', '2, 1'}
    assert get(False) == {'1, 2'}
    assert get(['unknown']) == set()

    def count(tags):
        return reader.get_entry_counts(tags=tags).total

    assert count(None) == 3
    assert count(['tag']) == 2
    assert count(['first']) == 1
    assert count(['unknown']) == 0
