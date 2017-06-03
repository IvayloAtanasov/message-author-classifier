const fs = require('fs');
const path = require('path');
const request = require('request');
const async = require('async');

const secrets = require('./secrets');

// TODO: 
// Private channels
// https://api.slack.com/methods/groups.list
// https://api.slack.com/methods/groups.history
// Group chats
// https://api.slack.com/methods/mpim.list
// https://api.slack.com/methods/mpim.history

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

    getChannelHistory(channelId, channelHistoryLimit, done) {
        request({
            baseUrl: this.baseUrl,
            uri: 'channels.history',
            method: 'POST',
            form: {
                token: this.secrets.accessToken,
                channel: channelId,
                count: channelHistoryLimit // 1-1000
            },
            json: true
        }, (err, res, body) => {
            if (err) return done(err);
            if (body.ok !== true) return done(new Error(`chanels.history request failed for channel ${channelId}`));

            // filter text messages only
            let messages = body.messages.filter(message => message.type === 'message' && message.subtype !== 'file_share');
            // leave text only, sort by user
            let messagesByUser = {};
            messages.forEach(message => {
                if (!Array.isArray(messagesByUser[message.user]))
                    messagesByUser[message.user] = [];

                messagesByUser[message.user].push(message.text);
            });
            let history = [];
            Object.keys(messagesByUser).forEach(userId => {
                history.push({user: userId, messages: messagesByUser[userId]});
            });

            return done(null, history);
        });
    }

    makeChannelsFile(channelsLimit = 999, channelHistoryLimit = 100) {
        let output = [];
        this.getChannels((err, channels) => {
            if (err) return console.error(err);

            channels = channels.slice(0, channelsLimit);
            async.eachSeries(channels, (channel, next) => {
                console.log(`Fetching history for channel ${channel.name}`);
                this.getChannelHistory(channel.id, channelHistoryLimit, (err, history) => {
                    if (err) return next(err);
                    output.push({channel: channel.id, history: history});

                    return next();
                });
            }, err => {
                if (err) return console.error(err);
                console.log('Fetching history done');
                // write into file
                fs.writeFile(path.join(this.outputDir, 'channels.json'), JSON.stringify(output), err => {
                    if (err) return console.log(`File write error: ${err}`);
                    console.log('makeChannelsFile - channels.json done');
                });
            });
        });
    }

    makeUsersFile() {
        this.getUsers((err, users) => {
            if (err) return console.error(err);
            fs.writeFile(path.join(this.outputDir, 'users.json'), JSON.stringify(users), err => {
                if (err) return console.log(`File write error: ${err}`);
                console.log('makeUsersFile - users.json done');
            });
        });
    }
}

const slack = new SlackDataLoader('slack-data', secrets.slack);
slack.makeChannelsFile(999, 1000);
slack.makeUsersFile();