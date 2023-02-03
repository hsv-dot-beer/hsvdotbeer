from itertools import count
from random import SystemRandom
from string import ascii_lowercase

from twitter.api import CHARACTER_LIMIT
from unittest import TestCase
from unittest.mock import patch

from tap_list_providers.twitter_api import ThreadedApi

FAKE_ID = count(1)

REAL_BREAKAGE = """We found 8 new beers!
- Cucumber Lime Seltzer from Chandlers Ford (style: Hard Seltzer) on tap at Chandlers Ford Brewing
- Cranberry Lemonade Seltzer from Chandlers Ford (style: Hard Seltzer) on tap at Chandlers Ford Brewing
- Island Thai’mmm from Chandlers Ford (style: Japanese Rice Lager) on tap at Chandlers Ford Brewing
- Nitro Stock Ale from Chandlers Ford (style: Old Ale) on tap at Chandlers Ford Brewing
- Chai Milk Stout from Chandlers Ford (style: Milk Stout) on tap at Chandlers Ford Brewing
- Pumpkin Pie Stout (Nitro) from Chandlers Ford (style: Other Stout) on tap at Chandlers Ford Brewing
- Big Beach Gose from Chandlers Ford (style: Fruited Gose) on tap at Chandlers Ford Brewing
- Brett Hazy Pale Ale from Chandlers Ford (style: Brett Beer) on tap at Chandlers Ford Brewing"""  # noqa


class FakeStatus:
    def __init__(self):
        self.id = next(FAKE_ID)


class TestThreadedApi(TestCase):
    def setUp(self):
        self.rng = SystemRandom()
        self.api = ThreadedApi()
        self.fake_last_status = None
        # just silence the config check
        # pylint: disable=protected-access
        self.api._config = True

    def test_single_tweet(self):
        msg = "This is a short message"
        with patch.object(self.api, "PostUpdate") as mock_post_update:
            self.api.PostUpdates(msg)
            mock_post_update.assert_called_once_with(status=msg)

    def test_chandlers_ford(self):
        """Test that the Chandlers Ford beers don't cause breakage"""
        split_tweets = self.api.split_tweet_by_lines(REAL_BREAKAGE, CHARACTER_LIMIT - 1)
        self.assertEqual(len(split_tweets), 4)
        for tweet in split_tweets:
            self.assertLess(len(tweet), CHARACTER_LIMIT, tweet)

    def test_long_tweet(self):
        words = [
            "".join(self.rng.choices(ascii_lowercase, k=25)) for dummy in range(25)
        ]
        msg = " ".join(words)

        def get_fake_id(status, in_reply_to_status_id=None):
            if not self.fake_last_status:
                self.assertIsNone(in_reply_to_status_id)
            else:
                self.assertEqual(in_reply_to_status_id, self.fake_last_status.id)

            self.assertIn(status, msg)
            next_status = FakeStatus()
            self.fake_last_status = next_status
            return next_status

        with patch.object(self.api, "PostUpdate") as mock_post_update:
            mock_post_update.side_effect = get_fake_id
            self.api.PostUpdates(msg, threaded=True)
            calls = mock_post_update.call_args_list
        # 625 chars + 50 spaces ==> 3 tweets
        self.assertEqual(len(calls), 3)

    def test_long_tweet_no_thread(self):
        words = [
            "".join(self.rng.choices(ascii_lowercase, k=25)) for dummy in range(25)
        ]
        msg = " ".join(words)

        def get_fake_id(status):
            self.assertIn(status, msg)
            next_status = FakeStatus()
            self.fake_last_status = next_status
            return next_status

        with patch.object(self.api, "PostUpdate") as mock_post_update:
            mock_post_update.side_effect = get_fake_id
            self.api.PostUpdates(msg, threaded=False)
            calls = mock_post_update.call_args_list
        # 625 chars + 50 spaces ==> 3 tweets
        self.assertEqual(len(calls), 3)

    def test_break_tweet_up_by_lines(self):
        tweet = "\r\n".join(
            [
                "Line 1",
                "Line 2",
                "Line 3",
                # line 4 is 301 chars. Yay.
                "This is an absurdly long line that will become the basis for what"
                " should be preserved as line 4 but who knows what Twitter will "
                "do. This needs even more filler since Twitter decided to double"
                " its tweet character limit. I have no idea what else to put in"
                " here because everything is awful. Enjoy Arby's.",
                "Line 5",
            ]
        )
        tweets = self.api.split_tweet_by_lines(
            tweet, character_limit=CHARACTER_LIMIT - len("…")
        )
        self.assertEqual(len(tweets), 3, tweets)
        self.assertEqual(
            tweets[0],
            "Line 1\r\nLine 2\r\nLine 3",
        )
        self.assertEqual(
            tweets[1],
            "This is an absurdly long line that "
            "will become the basis for what"
            " should be preserved as line 4 but who knows what Twitter will "
            "do. This needs even more filler since Twitter decided to double"
            " its tweet character limit. I have no idea what else to put in "
            "here because everything",
        )
        self.assertEqual(
            tweets[2],
            "is awful. Enjoy Arby's.\r\nLine 5",
        )
