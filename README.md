# Kio's Assistant

## 2 ways to setup email notifications

### 1. Using triggers

* Currently used.
* https://medium.com/@max.brawer/learn-to-magically-send-emails-from-your-google-form-responses-8bbdfd3a4d02

```javascript
function onFormSubmit(e) {  
  let json_body = {
        form_name : '[0k - 3k] Application for Kio\'s Academy Teams'
    };
    
  // Uncomment below to get all details submitted in the form
  // const values = e.namedValues;
  // for (let key in values) 
  //   json_body[key] = values[key]
  
    GmailApp.sendEmail('email@gmail.com', 'There is a new application for Academy Teams.', JSON.stringify(json_body));
}
```

### 2. Using inbuilt notification

* https://medium.com/zapier/how-to-get-customized-email-notifications-from-google-forms-with-a-hidden-feature-b08f1b941e38
* Forward emails to bot's address.

## Monitor Gmail using python

* https://codehandbook.org/how-to-read-email-from-gmail-using-python/
* https://stackoverflow.com/questions/33119667/reading-gmail-is-failing-with-imap

## Bot

Adding the bot:
https://discordapp.com/oauth2/authorize?&client_id=736823106194112593&scope=bot&permissions=8

## TODO

* Use discord logger
* Rewrite using [RoboDanny](https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/reminder.py)
  * Add prompts
  * Change lists to embeds and menus

## Changelog
### v2.0
* Refactored whole codebase
* Added Reminders


### v1.0
* First version with Google form monitoring
* Added new command `!!new_event` to create new events.
    * Format `!!new_event <event_name> :: <event_datetime>`
* Added new command `!!clear_event` to clear a single event.
    * Format `!!clear_event <event_id>`
* Added new command `!!clear_events` to clear all the existing events.
    * Format `!!clear_events`
* Added custom emoji for events
* Add more datetime details to new events.
