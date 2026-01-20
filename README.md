## 🚀 Deploy to Heroku

You can deploy this Telegram Music Bot to Heroku with just **one click**.

<p align="center">
  <a href="https://heroku.com/deploy?template=https://github.com/askimyavas7-tech/chee">
    <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy to Heroku">
  </a>
</p>

### 📋 Requirements
Before deploying, make sure you have:
- A Telegram account
- A Telegram Bot Token from **@BotFather**
- API_ID and API_HASH from https://my.telegram.org
- A MongoDB URL from https://cloud.mongodb.com
- A Pyrogram v2 String Session from **@StringFatherBot**

### ⚙️ Environment Variables
During deployment, Heroku will ask you to fill the following variables:

- `API_ID`
- `API_HASH`
- `BOT_TOKEN`
- `MONGO_URL`
- `LOGGER_ID`
- `OWNER_ID`
- `SESSION`

Fill them correctly and click **Deploy App**.

### ✅ Done!
Once the deployment is complete, turn on the **worker dyno** and your music bot will be online 🎶
