Relay feed and vcs activities to an IRC channel.

Installation
============

    git clone https://github.com/adamwight/slander

    pip install twisted feedparser PyYAML irc

OR

    apt-get install python-twisted python-feedparser python-yaml python-irclib

Configuration
=============

Config files are written in YAML, and are usually kept in the user's ".slander" or in /etc/slander

This is... sort of the configuration file used for the CiviCRM project:

    jobs:
        svn:
            root: http://svn.civicrm.org/civicrm
            args: --username SVN_USER --password SVN_PASSS
            changeset_url_format:
                https://fisheye2.atlassian.com/changelog/CiviCRM?cs=%s

        jira:
            base_url:
                http://issues.civicrm.org/jira
            source:
                http://issues.civicrm.org/jira/activity?maxResults=20&streams=key+IS+CRM&title=undefined

        # Gentle reader, now you know I'm lying and that the CiviCRM project
        # does not use Mingle...  Anyway, grab this URL from Mingle's History
        # -> All page.
        mingle:
            source:
                https://wikimedia.mingle.thoughtworks.com/projects/online_fundraiser/feeds/WOjFYsRs1T04NhsqTdnSOA.atom

    irc:
        host: irc.freenode.net
        port: 6667
        nick: civi-activity
        # Optional unless your bot is registered
        pass: FOO
        realname: CiviCRM svn and jira notification bot
        # Note that quotes are necessary around #channames
        channel: "#civicrm-test"
        # Truncate messages longer than this many characters
        maxlen: 200

    # Measured in seconds
    poll_interval: 60

    # Override the builtin URL if you have forked this project, so people know
    # how to contribute.
    source_url: https://svn.civicrm.org/tools/trunk/bin/scripts/ircbot-civi.py

Running
=======

To start the bot, call

    ./slander/slander.py

If you want to specify a config file, pass it as an argument:

    ./slander/slander.py /etc/slander/PROJ.yaml

Alternatively, you can give just the project name, and slander will look in /etc/slander/PROJ.yaml:

    ./slander/slander.py PROJ

Credits
=======
IRC code adapted from Miki Tebeka's http://pythonwise.blogspot.com/2009/05/subversion-irc-bot.html

Markup stripper from Eloff's http://stackoverflow.com/a/925630

Written by Adam Roses Wight

The project homepage is https://github.com/adamwight/slander
