# Domo-HelpdeskMafia

## To create a slackbot

1. Go to your Slack App settings (api.slack.com/apps)
2. Under "Event Subscriptions", enable events
3. Subscribe to these bot events:

   - message.channels
   - app_mentions

4. Also verify that your bot has been:
   - Added to the channel you're testing in
   - Given the necessary OAuth scopes: chat:write, app_mentions:read, channels:history
