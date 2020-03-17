import dataclasses
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union

# TODO: remove this once we drop support for Python 3.7
if sys.version_info >= (3, 8):  # pragma: no cover
    from typing import Protocol, runtime_checkable, Literal
else:  # pragma: no cover
    from typing_extensions import Protocol, runtime_checkable, Literal


_T = TypeVar('_T')


class _namedtuple_compat:

    """Add namedtuple-like methods to a dataclass."""

    @classmethod
    def _make(cls: Type[_T], iterable: Iterable[Any]) -> _T:
        iterable = tuple(iterable)
        attrs_len = len(dataclasses.fields(cls))
        if len(iterable) != attrs_len:
            raise TypeError(
                'Expected %d arguments, got %d' % (attrs_len, len(iterable))
            )
        return cls(*iterable)

    _replace = dataclasses.replace

    _asdict = dataclasses.asdict


# Public API


@dataclass(frozen=True)
class Feed(_namedtuple_compat):

    """Data type representing a feed."""

    #: The URL of the feed.
    url: str

    #: The date the feed was last updated.
    updated: Optional[datetime] = None

    #: The title of the feed.
    title: Optional[str] = None

    #: The URL of a page associated with the feed.
    link: Optional[str] = None

    #: The author of the feed.
    author: Optional[str] = None

    #: User-defined feed title.
    user_title: Optional[str] = None


@dataclass(frozen=True)
class Entry(_namedtuple_compat):

    """Data type representing an entry."""

    #: Entry identifier.
    id: str

    # Entries returned by the parser always have updated set.
    # I tried modeling this through typing, but it's too complicated.
    # TODO: Make typing enforce updated is always set.
    # TODO: When can be Entry.updated be None anyway?

    #: The date the entry was last updated.
    updated: Optional[datetime]

    #: The title of the entry.
    title: Optional[str] = None

    #: The URL of a page associated with the entry.
    link: Optional[str] = None

    #: The author of the feed.
    author: Optional[str] = None

    #: The date the entry was first published.
    published: Optional[datetime] = None

    #: A summary of the entry.
    summary: Optional[str] = None

    #: Full content of the entry.
    #: A sequence of :class:`Content` objects.
    content: Sequence['Content'] = ()

    #: External files associated with the entry.
    #: A sequence of :class:`Enclosure` objects.
    enclosures: Sequence['Enclosure'] = ()

    #: Whether the entry was read or not.
    read: bool = False

    #: Whether the entry is important or not.
    important: bool = False

    #: The entry's feed.
    feed: Optional[Feed] = None


@dataclass(frozen=True)
class Content(_namedtuple_compat):

    """Data type representing a piece of content."""

    #: The content value.
    value: str

    #: The content type.
    type: Optional[str] = None

    #: The content language.
    language: Optional[str] = None


@dataclass(frozen=True)
class Enclosure(_namedtuple_compat):

    """Data type representing an external file."""

    #: The file URL.
    href: str

    #: The file content type.
    type: Optional[str] = None

    #: The file length.
    length: Optional[int] = None


@dataclass(frozen=True)
class EntrySearchResult(_namedtuple_compat):

    """Data type representing the result of an entry search."""

    id: str

    # TODO: is this the right way to expose the feed?
    feed: str

    title: Optional[str]

    # TODO: more fields


# Semi-public API (typing support)


# TODO: Could we use some kind of str-compatible enum here?
FeedSortOrder = Literal['title', 'added']


# https://github.com/python/typing/issues/182
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONType = Union[Dict[str, JSONValue], List[JSONValue]]


# Using protocols here so we have both duck typing and type checking.
# Simply catching AttributeError (e.g. on feed.url) is not enough for mypy,
# see https://github.com/python/mypy/issues/8056.


@runtime_checkable
class FeedLike(Protocol):

    # We don't use "url: str" because we don't care if url is writable.

    @property
    def url(self) -> str:  # pragma: no cover
        ...


@runtime_checkable
class EntryLike(Protocol):
    @property
    def id(self) -> str:  # pragma: no cover
        ...

    @property
    def feed(self) -> FeedLike:  # pragma: no cover
        ...


FeedInput = Union[str, FeedLike]
EntryInput = Union[Tuple[str, str], EntryLike]


def feed_argument(feed: FeedInput) -> str:
    if isinstance(feed, FeedLike):
        return feed.url
    if isinstance(feed, str):
        return feed
    raise ValueError('feed')


def entry_argument(entry: EntryInput) -> Tuple[str, str]:
    if isinstance(entry, EntryLike):
        return feed_argument(entry.feed), entry.id
    if isinstance(entry, tuple) and len(entry) == 2:
        feed_url, entry_id = entry
        if isinstance(feed_url, str) and isinstance(entry_id, str):
            return entry
    raise ValueError('entry')


# Private API
# https://github.com/lemon24/reader/issues/111


class ParsedFeed(NamedTuple):

    feed: Feed
    http_etag: Optional[str]
    http_last_modified: Optional[str]


class ParseResult(NamedTuple):

    parsed_feed: ParsedFeed
    entries: Iterable[Entry]

    # compatibility / convenience

    @property
    def feed(self) -> Feed:
        return self.parsed_feed.feed

    @property
    def http_etag(self) -> Optional[str]:
        return self.parsed_feed.http_etag

    @property
    def http_last_modified(self) -> Optional[str]:
        return self.parsed_feed.http_last_modified


class FeedForUpdate(NamedTuple):

    """Update-relevant information about an exiting feed, from Storage."""

    url: str

    #: The date the feed was last updated, according to the feed.
    updated: Optional[datetime]

    http_etag: Optional[str]
    http_last_modified: Optional[str]

    #: Whether the next update should update *all* entries,
    #: regardless of their .updated.
    stale: bool

    #: The date the feed was last updated, according to reader; none if never.
    last_updated: Optional[datetime]


class EntryForUpdate(NamedTuple):

    """Update-relevant information about an exiting entry, from Storage."""

    #: The date the entry was last updated, according to the entry.
    updated: datetime


class FeedUpdateIntent(NamedTuple):

    """Data to be passed to Storage when updating a feed."""

    url: str

    #: The time at the start of updating this feed.
    last_updated: datetime

    feed: Optional[Feed] = None
    http_etag: Optional[str] = None
    http_last_modified: Optional[str] = None


class EntryUpdateIntent(NamedTuple):

    """Data to be passed to Storage when updating a feed."""

    #: The feed URL.
    url: str

    #: The entry.
    entry: Entry

    #: The time at the start of updating this feed (start of update_feed
    #: in update_feed, the start of each feed update in update_feeds).
    last_updated: datetime

    #: The time at the start of updating this batch of feeds (start of
    #: update_feed in update_feed, start of update_feeds in update_feeds);
    #: None if the entry already exists.
    first_updated_epoch: Optional[datetime]

    #: The index of the entry in the feed (zero-based).
    feed_order: int


class UpdatedEntry(NamedTuple):

    entry: Entry
    new: bool


class UpdateResult(NamedTuple):

    #: The entries that were updated.
    entries: Iterable[UpdatedEntry]


# TODO: these should probably be in storage.py (along with some of the above)


class EntryFilterOptions(NamedTuple):

    """Options for filtering the results of the "get entry" storage methods."""

    feed_url: Optional[str] = None
    entry_id: Optional[str] = None
    read: Optional[bool] = None
    important: Optional[bool] = None
    has_enclosures: Optional[bool] = None
