import datetime

from reader import Content
from reader import Enclosure
from reader.types import EntryData
from reader.types import FeedData


feed = FeedData(url='{}empty.rss'.format(url_base))

entries = [
    EntryData(
        feed_url=feed.url, id='7bd204c6-1655-4c27-aeee-53f933c5395f', updated=None
    )
]
