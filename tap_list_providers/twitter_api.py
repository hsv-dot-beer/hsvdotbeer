from twitter.api import Api, CHARACTER_LIMIT


class ThreadedApi(Api):

    def PostUpdates(
        self, status, continuation=None, threaded=False, **kwargs
    ):
        """Post one or more twitter status messages from the authenticated user.
        Unlike api.PostUpdate, this method will post multiple status updates
        if the message is longer than CHARACTER_LIMIT characters.
        Args:
          status:
            The message text to be posted.
            May be longer than CHARACTER_LIMIT characters.
          continuation:
            The character string, if any, to be appended to all but the
            last message.  Note that Twitter strips trailing '...' strings
            from messages.  Consider using the unicode \u2026 character
            (horizontal ellipsis) instead. [Defaults to None]
          threaded:
            If True, makes each additional status message a reply to the
            previous one. [Defaults to False]
          **kwargs:
            See api.PostUpdate for a list of accepted parameters.
        Returns:
          A of list twitter.Status instance representing the messages posted.
        """
        results = list()

        if continuation is None:
            continuation = ''
        char_limit = CHARACTER_LIMIT - len(continuation)

        tweets = self.split_tweet_by_lines(
            tweet=status, character_limit=char_limit,
        )

        if len(tweets) == 1:
            results.append(self.PostUpdate(status=tweets[0], **kwargs))
            return results
        last_reply_to_id = None
        for tweet in tweets[0:-1]:
            if threaded and last_reply_to_id is not None:
                # use the not none check here so we don't override the caller
                # if they're tweeting a series of updates in response to
                # an existing status
                kwargs['in_reply_to_status_id'] = last_reply_to_id
            latest_tweet = self.PostUpdate(status=tweet + continuation, **kwargs)
            last_reply_to_id = latest_tweet.id
            results.append(latest_tweet)

        if threaded:
            kwargs['in_reply_to_status_id'] = last_reply_to_id
        results.append(self.PostUpdate(status=tweets[-1], **kwargs))

        return results

    def split_tweet_by_lines(self, tweet, character_limit):
        """Break the thread up by lines if possible"""
        lines = tweet.split('\r\n')
        tweets = []
        current_tweet = ''

        for line in lines:
            if len(line) > character_limit:
                # this line is too long.
                # dump what we have into the tweet queue
                # and then use upstream's method to split up this line
                if current_tweet:
                    tweets.append(current_tweet)
                    current_tweet = ''
                split = self._TweetTextWrap(line, char_lim=character_limit)
                # and then take whatever it gave us
                # as a series of tweets
                tweets += split[:-1]
                # keep the last line as the start of our next tweet
                current_tweet = split[-1]
                continue
            if len(line) + len(current_tweet) >= character_limit:
                # next tweet!
                if current_tweet:
                    tweets.append(current_tweet)
                current_tweet = line
                continue
            # add the next line to the currently being built tweet
            if current_tweet:
                current_tweet = f'{current_tweet}\r\n{line}'
            else:
                current_tweet = line
        if current_tweet:
            # if we have anything left over, tack it on!
            tweets.append(current_tweet)
        return tweets
