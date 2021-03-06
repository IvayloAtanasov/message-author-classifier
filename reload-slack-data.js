const fs = require('fs');
const path = require('path');
const request = require('request');
const async = require('async');

const secrets = require('./secrets');

class SlackDataLoader {

    constructor(outputDir, secrets) {
        this.baseUrl = 'https://slack.com/api';
        this.outputDir = outputDir;
        this.secrets = secrets;
    }

    getUsers(done) {
        request({
            baseUrl: this.baseUrl,
            uri: 'users.list',
            method: 'POST',
            form: {
                token: this.secrets.accessToken
            },
            json: true
        }, (err, res, body) => {
            if (err) return done(err);
            if (body.ok !== true) return done(new Error('users.list request failed'));

            let users = body.members.filter(user => !user.deleted && !user.is_bot);
            users = users.map(user => {
                let { id, name, real_name } = user;
                return { id, name, real_name };
            });

            return done(null, users);
        });
    }

    getChannels(done) {
        request({
            baseUrl: this.baseUrl,
            uri: 'channels.list',
            method: 'POST',
            form: {
                token: this.secrets.accessToken,
                exclude_members: true
            },
            json: true
        }, (err, res, body) => {
            if (err) return done(err);
            if (body.ok !== true) return done(new Error('chanels.list request failed'));

            let channels = body.channels.map(channel => {
                return {
                    id: channel.id,
                    name: channel.name
                };
            });

            return done(null, channels);
        });
    }

    getPrivateChannels(done) {
        request({
            baseUrl: this.baseUrl,
            uri: 'groups.list',
            method: 'POST',
            form: {
                token: this.secrets.accessToken
            },
            json: true
        }, (err, res, body) => {
            if (err) return done(err);
            if (body.ok !== true) return done(new Error('groups.list request failed'));

            let channels = body.groups.map(channel => {
                return {
                    id: channel.id,
                    name: channel.name
                };
            });

            return done(null, channels);
        });
    }

    getChannelHistory(channelId, isPrivate, channelHistoryLimit, done) {
        let uri = isPrivate ? 'groups.history' : 'channels.history';
        const maxEntriesPerPage = 1000; // 1-1000

        let fetchLimit = maxEntriesPerPage;
        if (channelHistoryLimit < maxEntriesPerPage) fetchLimit = channelHistoryLimit;
        let latest = null;

        const results = [];
        async.doUntil(next => {
            request({
                baseUrl: this.baseUrl,
                uri: uri,
                method: 'POST',
                form: {
                    token: this.secrets.accessToken,
                    channel: channelId,
                    count: fetchLimit,
                    latest: latest
                },
                json: true
            }, (err, res, body) => {
                if (err) return next(err);
                if (body.ok !== true) return next(new Error(`channels.history request failed for channel ${channelId}`));

                console.log(`channels.history request fetched ${body.messages.length} messages for channel ${channelId}`);
                results.push(body);

                return next(null, body);
            });
        }, body => {
            channelHistoryLimit -= fetchLimit;
            if (channelHistoryLimit < maxEntriesPerPage) fetchLimit = channelHistoryLimit;

            // get last record timestamp to be used as starting point into next request
            if (body.messages.length > 0)
                latest = body.messages[body.messages.length - 1].ts;

            // continue fetching if there are more entries in channel and limit is not reached
            return !body.has_more || fetchLimit === 0;
        }, err => {
            // Note: 2nd cb param seems to be the last returned result, not array of all. Used custom results holder.
            if (err) return done(err);

            let messagesByUser = {};
            results.forEach(body => {
                // filter text messages only
                let messages = body.messages.filter(message => message.type === 'message' && message.subtype !== 'file_share');
                // leave text only, sort by user
                messages.forEach(message => {
                    if (!Array.isArray(messagesByUser[message.user]))
                        messagesByUser[message.user] = [];

                    messagesByUser[message.user].push(message.text);
                });
            });

            let history = [];
            Object.keys(messagesByUser).forEach(userId => {
                history.push({user: userId, messages: messagesByUser[userId]});
            });

            return done(null, history);
        });
    }

    makeChannelsFile(channelsLimit, channelHistoryLimit, done) {
        let output = [];
        this.getChannels((err, channels) => {
            if (err) return done(err);

            channels = channels.slice(0, channelsLimit);
            async.eachSeries(channels, (channel, next) => {
                console.log(`Fetching history for channel ${channel.name}`);
                this.getChannelHistory(channel.id, false, channelHistoryLimit, (err, history) => {
                    if (err) return next(err);
                    output.push({channel: channel.id, history: history});

                    return next();
                });
            }, err => {
                if (err) return done(err);
                // write into file
                fs.writeFile(path.join(this.outputDir, 'channels.json'), JSON.stringify(output), err => {
                    if (err) return done(err);
                    console.log('makeChannelsFile - channels.json done');
                    return done();
                });
            });
        });
    }

    // TODO: reuse from makeChannelsFile?
    makePrivateChannelsFile(channelsLimit, channelHistoryLimit, done) {
        let output = [];
        this.getPrivateChannels((err, channels) => {
            if (err) return done(err);

            channels = channels.slice(0, channelsLimit);
            async.eachSeries(channels, (channel, next) => {
                console.log(`Fetching history for private channel ${channel.name}`);
                this.getChannelHistory(channel.id, true, channelHistoryLimit, (err, history) => {
                    if (err) return next(err);
                    output.push({channel: channel.id, history: history});

                    return next();
                });
            }, err => {
                if (err) return done(err);
                // write into file
                fs.writeFile(path.join(this.outputDir, 'privateChannels.json'), JSON.stringify(output), err => {
                    if (err) return done(err);
                    console.log('makePrivateChannelsFile - privateChannels.json done');
                    return done();
                });
            });
        });
    }

    makeUsersFile(done) {
        this.getUsers((err, users) => {
            if (err) return done(err);
            fs.writeFile(path.join(this.outputDir, 'users.json'), JSON.stringify(users), err => {
                if (err) return done(err);
                console.log('makeUsersFile - users.json done');
                return done();
            });
        });
    }
}

const slack = new SlackDataLoader('slack-data', secrets.slack);
async.series([
    next => { slack.makeUsersFile(next); },
    next => { slack.makeChannelsFile(999, 10000, next); },
    next => { slack.makePrivateChannelsFile(999, 10000, next); }
], err => {
    if (err) {
        console.error(err);
    } else {
        console.log('DONE');
    }
});
